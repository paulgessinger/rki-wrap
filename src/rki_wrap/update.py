import datetime
import pandas as pd
import requests
import click
import time
import random
from flask import current_app
from sqlalchemy import select

from rki_wrap import config
from rki_wrap.model import db, Entry

def update_arcgis():
    df = pd.read_csv(config.SOURCE_URL)
    df.Aktualisierung = pd.to_datetime(df.Aktualisierung)
    ger_inc_upd = df.Aktualisierung.iloc[0]

    # do we have entries for this date already?
    n_existing = Entry.query.filter(Entry.date == ger_inc_upd.date()).count()
    if n_existing == 0:
        total_inhabitants = df.LAN_ew_EWZ.sum()
        weighted = df.LAN_ew_EWZ / total_inhabitants * df.cases7_bl_per_100k
        ger_inc_7d = weighted.sum()

        for idx, row in df.iterrows():
            e = Entry(
                date=row.Aktualisierung.date(),
                loc=row.LAN_ew_GEN,
                inc_7d=row.cases7_bl_per_100k,
            )
            db.session.add(e)
            # print(row.cases7_bl_per_100k)

        e = Entry(date=ger_inc_upd.date(), loc="Deutschland", inc_7d=ger_inc_7d)
        db.session.add(e)
        db.session.commit()

def update_rki_excel():
    r = requests.get(config.EXCEL_SOURCE_URL)
    df = pd.read_excel(r.content, engine="openpyxl", sheet_name="BL_7-Tage-Inzidenz (fixiert)")
    df = df.transpose()
    locs = list(df.iloc[0])
    df = df.drop(df.index[0])
    date_i = 0
    for l in locs:
        if pd.isnull(l):
            date_i +=1 
        else:
            break
    date_i -= 1
    columns = list(locs)
    columns[date_i] = "date"
    df.columns = columns
    df.index = pd.to_datetime(df.date)

    locs = [str(l) for l in locs if not pd.isnull(l)]
    current_app.logger.debug("locs: %s", locs)
    assert len(locs) == 17
    df = df[locs]

    n_added = 0
    n_updated = 0

    for idx, row in df.iterrows():
        for k, v in row.items():
            loc = k if k != "Gesamt" else "Deutschland"
            e = Entry.query.filter((Entry.date == idx.date() ) & (Entry.loc == loc)).first()
            if e is not None:
                #  print(idx, "exists")
                if e.inc_7d != v:
                    e.inc_7d = v
                    n_updated += 1
            else:
                #  print(idx, "not exists")
                e = Entry(date=idx.date(), loc=loc, inc_7d=v)
                db.session.add(e)
                n_added += 1
    db.session.commit()

    current_app.logger.info("Added %u entries and updated %u", n_added, n_updated)


def add_commands(app):
    @app.cli.command("update")
    @click.option("--jitter", envvar="UPDATE_JITTER_SECONDS", default=0)
    def run_update(jitter: int):

        delay = random.randint(0, jitter)
        print("Sleeping for", delay, "seconds")
        time.sleep(delay)

        if config.HEALTHCHECK_URL is not None:
            requests.get(config.HEALTHCHECK_URL + "/start", timeout=10)

        try:

            arcgis_failed = False
            rki_excel_failed = False
        
            try:
                update_arcgis()
                current_app.logger.info("Arcgis update succeeded")
            except:
                arcgis_failed = True
                current_app.logger.error("Arcgis update failed", exc_info=True)

            try:
                update_rki_excel()
                current_app.logger.info("RKI excel update succeeded")
            except:
                rki_excel_failed = True
                current_app.logger.error("RKI excel update failed", exc_info=True)
    
            if arcgis_failed and rki_excel_failed:
                raise RuntimeError("All update methods failed")

                
            if config.HEALTHCHECK_URL is not None:
                requests.get(config.HEALTHCHECK_URL, timeout=10)
        except:
            if config.HEALTHCHECK_URL is not None:
                requests.get(config.HEALTHCHECK_URL + "/fail", timeout=10)
            raise

    @app.cli.command("show")
    def show():
        for entry in Entry.query.filter(
            Entry.date > datetime.date.today() - config.DATE_WINDOW
        ).all():
            print(entry.loc, entry.date, entry.inc_7d)
