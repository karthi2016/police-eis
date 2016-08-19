import numpy as np
import pandas as pd
import yaml
import logging
import sys
import argparse
import pickle
import psycopg2
import datetime
import time
import pdb

from . import setup_environment, models, scoring
from . import dataset, experiment
from . import populate_features

def main(config_file_name, args):

    if len(args.featuretable) < 2:
        log_filename = "logs/build_{}.log".format(datetime.datetime.now().strftime("%Y%m%d-%H:%M"))
    else:
        log_filename = "logs/model_{}.log".format(datetime.datetime.now().strftime("%Y%m%d-%H:%M"))

    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        level=logging.DEBUG,
                        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()])
    log = logging.getLogger('eis')

    try:
        with open(config_file_name, 'r') as f:
            config = yaml.load(f)
        log.info("Loaded experiment file: {}".format(config_file_name))
    except:
        log.exception("Failed to get experiment configuration file!")
        raise

    # if no features table name was set by the user, 
    # set the features table name based on type of prediction (officer / dispatch)
    if ( args.featuretable):
        table_name = args.featuretable
    else:
        table_name = '{}_features'.format(config['unit'])

    # read table name from config file
    # NOTE!!!! this breaks the command line passing of table name
    table_name = config["dispatch_feature_table_name"]

    log.debug("feature table name: {}".format(table_name))

    # If asked to generate features, then do that and stop.
    if args.buildfeatures:

        log.info("Re-building features...")

        # Create the features table.
        populate_features.create_features_table(config, table_name)

        # Populate the featuress table
        populate_features.populate_features_table(config, table_name)

        log.info('Done creating features table')
        sys.exit()

    all_experiments = experiment.generate_models_to_run(config)

    log.info("Running models on dataset...")
    batch_timestamp = datetime.datetime.now().isoformat()
    for my_exp in all_experiments:
        start = time.time()
        timestamp = datetime.datetime.now().isoformat()

        result_y, result_y_binary, importances, modelobj, individual_imps = models.run(
            my_exp.exp_data["train_x"],
            my_exp.exp_data["train_y"],
            my_exp.exp_data["test_x"],
            my_exp.config["model"],
            my_exp.config["parameters"],
            my_exp.config["n_cpus"])

        # required for to_save dict below, (legacy code)
        groupscores = []
        confusion_matrices = []

        # TODO: make this more robust for officer vs dispatch level predictions
        end = time.time()
        #pdb.set_trace()
        model_time_in_seconds = "%.3f" % (end-start)

        if config['unit'] == 'officer':
            to_save = {"test_labels": my_exp.exp_data["test_y"],
                       "test_predictions": result_y,
                       "test_predictions_binary" : result_y_binary,
                       "config": my_exp.config,
                       "officer_id_train": my_exp.exp_data["train_x_index"],
                       "officer_id_test": my_exp.exp_data["test_x_index"],
                       "features": my_exp.exp_data["names"],
                       "timestamp": timestamp,
                       "parameters": my_exp.config["parameters"],
                       "train_start_date": my_exp.exp_data["train_start_date"],
                       "test_end_date": my_exp.exp_data["test_end_date"],
                       "feature_importances": importances,
                       "feature_importances_names": my_exp.exp_data["features"],
                       "aggregation": groupscores,
                       "eis_baseline": confusion_matrices,
                       "modelobj": modelobj,
                       "individual_importances": individual_imps,
                       "time_for_model_in_seconds": model_time_in_seconds }

        elif config['unit'] == 'dispatch':
            to_save = {"test_labels": my_exp.exp_data["test_y"],
                       "test_predictions": result_y,
                       "test_predictions_binary": result_y_binary,
                       "config": my_exp.config,
                       "timestamp": timestamp,
                       "parameters": my_exp.config["parameters"],
                       "feature_importances_names": my_exp.exp_data["features"],
                       "modelobj": modelobj,
                       "time_for_model_in_seconds": model_time_in_seconds }

        # get all model metrics.
        all_metrics = scoring.calculate_all_evaluation_metrics( list( my_exp.exp_data["test_y"]), list(result_y), list(result_y_binary), model_time_in_seconds )

        # pickle all the model data (everything in the to_save dict)
        model_filename = "{}/{}_{}.pkl".format(config["directory"].strip('/'), config["pkl_prefix"], timestamp)
        pickle_results(model_filename, to_save)

        # package data for storing into results schema.
        unit_id_train    = list( my_exp.exp_data["train_x_index"] )
        unit_id_test     = list( my_exp.exp_data["test_x_index"] )
        unit_predictions = list( result_y )
        unit_labels      = list( my_exp.exp_data["test_y"] )

        # Store information about this experiment into the results schema.
        log.debug("storing model information")
        dataset.store_model_info( timestamp, batch_timestamp, my_exp.config)
        log.debug("storing predictions information")
        dataset.store_prediction_info( timestamp, unit_id_train, unit_id_test, unit_predictions, unit_labels )
        log.debug("storing evaluation metric information")
        dataset.store_evaluation_metrics( timestamp, all_metrics )

    log.info("Done!")
    return None


def pickle_results(pkl_file, to_save):
    """
    Save contents of experiment to pickle file for later use
    """

    with open(pkl_file, 'wb') as f:
        pickle.dump(to_save, f, protocol=pickle.HIGHEST_PROTOCOL)

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="pass your config", default="default.yaml")
    parser.add_argument( "-b", "--buildfeatures", help="build the features and stop", action='store_true' )
    parser.add_argument( "-f", "--featuretable", help="set the name of the features table", default="features" )
    args = parser.parse_args()
    main(args.config, args)
