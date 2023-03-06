import logging
import os.path
from argparse import ArgumentParser
from configparser import ConfigParser
from glob import glob

from modules.utils import DEFAULT_ENCODING
from modules.generation import create_zip_file
from modules.stats import get_zip_stats, stats_to_csv_data

DEFAULT_CONFIG = 'config.default.ini'
MODES = ['create', 'analyze']
ZIPFILE_SEARCH_TEMPLATE = '*.zip'

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # Args parsing
    parser = ArgumentParser()
    parser.add_argument('-m',
                        '--mode',
                        type=str,
                        choices=MODES,
                        help='Mode switch. Allows user to create zip archives or to analyze their contents',
                        required=True)
    parser.add_argument('-w',
                        '--workdir',
                        type=str,
                        help='Directory to create files in or to analyze files from',
                        required=True)
    parser.add_argument('-c',
                        '--config',
                        type=str,
                        help='Override default config with given file')

    args = parser.parse_args()
    logging.debug(f"Args: {args}")

    # Config file loading
    config = ConfigParser()
    read_ok = False
    for conf_candidate in [args.config, DEFAULT_CONFIG]:
        if not conf_candidate:
            continue

        logging.debug(f'Trying to read config file')

        # read_ok - list of successfully read configs
        read_ok = config.read(conf_candidate, encoding=DEFAULT_ENCODING)
        if not read_ok:
            logging.error(f'Failed to read custom config: {conf_candidate}')
            continue
        else:
            logging.info(f'Config file loaded: {conf_candidate}')

    if not read_ok:
        logging.error(f'No config file! Script needs "-c" option or file "{DEFAULT_CONFIG}"')
        exit(1)

    # Main logic
    if args.mode == MODES[0]:
        # create zips
        logging.debug("Starting ZIPs generation")

        tgt_path = os.path.abspath(args.workdir)
        os.makedirs(tgt_path, exist_ok=True)

        # possible place for optimization (io-bound loop -> can be splitted to threads)
        for i in range(config.getint('main', 'zips')):
            zip_buffer = create_zip_file(config.getint('main', 'xmls'))
            zip_fname = os.path.join(
                args.workdir,
                config['main']['zipname_template'].format(i)
            )
            with open(zip_fname, 'wb') as f:
                f.write(zip_buffer.getvalue())

        logging.info("ZIPs successfully generated")

    if args.mode == MODES[1]:
        # analyze zips
        logging.debug("Starting ZIPs analysis")
        search_template = os.path.join(args.workdir, ZIPFILE_SEARCH_TEMPLATE)
        file_list = glob(search_template)

        processed_files = []
        all_stats = []
        for fname in file_list:
            logging.debug(f"Processing file: {fname}")
            zip_stats = get_zip_stats(fname)
            if zip_stats:
                processed_files.append(fname)
                all_stats.extend(zip_stats)
            else:
                logging.info(f"ZIP {fname} is empty or was not processed due to errors")

        csv_1_name = config['main']['csvname_template'].format("id-level")
        csv_2_name = config['main']['csvname_template'].format("id-objname")

        csv_1_name = os.path.join(args.workdir, csv_1_name)
        csv_2_name = os.path.join(args.workdir, csv_2_name)

        data1, data2 = stats_to_csv_data(all_stats)

        with open(csv_1_name, "wb") as f:
            f.write(data1)

        with open(csv_2_name, "wb") as f:
            f.write(data2)

        logging.info(f"Files {csv_1_name} and {csv_2_name} succesfully created")
