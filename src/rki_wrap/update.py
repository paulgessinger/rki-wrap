import datetime
import pandas as pd
import requests

from rki_wrap import config
from rki_wrap.model import db, Entry


def run_update():

    if config.HEALTHCHECK_URL is not None:
        requests.get(config.HEALTHCHECK_URL + "/start", timeout=10)

    try:
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

        if config.HEALTHCHECK_URL is not None:
            requests.get(config.HEALTHCHECK_URL, timeout=10)
    except:
        if config.HEALTHCHECK_URL is not None:
            requests.get(config.HEALTHCHECK_URL + "/fail", timeout=10)
        raise


def show():
    for entry in Entry.query.filter(
        Entry.date > datetime.date.today() - config.DATE_WINDOW
    ).all():
        print(entry.loc, entry.date, entry.inc_7d)
