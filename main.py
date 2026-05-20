#!/usr/bin/env python3
import argparse
import os
import yaml
import logging
from database.db import Database


class FileNotExists(Exception):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="VPN сервис")
    parser.add_argument("-db", "--database", type=str, default="db.sqlite", required=False, help="Путь до файла базы данных")
    parser.add_argument("-s", "--schema", type=str, default="config.yaml", required=False, help="Путь до схемы базы")
    parser.add_argument("-l", "--logname", type=str, default="vpn_logger", required=False, help="Имя логгера")

    args = parser.parse_args()
    logger = logging.getLogger(args.logname)

    if not os.path.exists(args.schema) or not os.path.isfile(args.schema):
        raise FileNotExists
    
    with open(args.schema, "r") as f:
        schema = yaml.safe_load(f)
    db = Database(args.database)
    db.create_database(schema)
