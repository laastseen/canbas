#!/usr/bin/env python3
"""Seed the database with demo data. Usage: python seed.py [--force]"""

import argparse

from run import app
from app.extensions import db
from app.seed_data import seed_database


def main():
    parser = argparse.ArgumentParser(description="Fill Canbas DB with demo data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear existing data and reseed",
    )
    args = parser.parse_args()

    with app.app_context():
        if args.force:
            from app.seed_data import clear_database
            clear_database()
        else:
            db.create_all()
        seed_database(force=args.force)


if __name__ == "__main__":
    main()
