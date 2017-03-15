from flask import Flask, render_template, request
from flask_cache import Cache
from flask_admin import Admin

from pymongo import MongoClient

from models import ResultadoView
from db_config import uri

app = Flask(__name__)
admin = Admin(app)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

#necessary for sessions
app.config['SECRET_KEY'] = '123456790'

db = MongoClient(uri).futbol_sma

admin.add_view(ResultadoView(db.resultados, 'Resultado'))


@app.route('/', methods=['GET'])
def main():

    division = request.args.get('division')
    if division not in ['primera', 'reserva']:
        division = 'primera'

    titulos = ['Posicion', 'Equipo', 'Puntos', 'PJ', 'PG', 'PE', 'PP', 'GF', 'GE', 'DG']
    tabla = get_posiciones(division)


    return render_template('tabla.html', rank=tabla, rank_head = titulos, division=division.capitalize())


from collections import Counter


@cache.memoize(timeout=1000)
def get_posiciones(division='primera', year=2017):
    for doc in db.posiciones.find({'division':division}).sort('tstamp', -1):
        tabla = doc['posiciones']
        return tabla


@cache.memoize(timeout=100)
def calcular_posiciones(division='primera', year=2017):

    col = db.resultados

    col.create_index('division')
    col.create_index('year')

    query = {'division':division, 'campeonato':year}

    equipos = set()

    pg = Counter()
    pp = Counter()
    pe = Counter()

    gf = Counter()
    gc = Counter()


    for doc in col.find(query):
        equipo1 = doc['equipo1']
        equipo2 = doc['equipo2']

        equipos.update([equipo1, equipo2])

        gano1 = None

        if doc['goles1'] > doc['goles2']:
            gano1 = True

        elif doc['goles2'] > doc['goles1']:
            gano1 = False

        pg[equipo1] += (gano1 is True)
        pp[equipo2] += (gano1 is True)

        pg[equipo2] += (gano1 is False)
        pp[equipo1] += (gano1 is False)

        pe[equipo1] += (gano1 is None)
        pe[equipo2] += (gano1 is None)

        gf[equipo1] += doc['goles1']
        gf[equipo2] += doc['goles2']

        gc[equipo1] += doc['goles2']
        gc[equipo2] += doc['goles1']

    # calculos finales y ranking
    # Posicion	Equipo	Puntos	PJ	PG	PE	PP	GF	GE	DG
    puntos = Counter()
    pj = Counter()
    dg = Counter()

    for team in equipos:
        puntos[team] = pg[team]*3 + pe[team]
        pj[team] = pg[team] + pe[team] + pp[team]
        dg[team] = gf[team] - gc[team]

    ranking = []

    rank = 0
    for equipo, _ in puntos.most_common():
        rank += 1
        ranking.append([rank, equipo, puntos[equipo], pj[equipo], pg[equipo], pe[equipo], pp[equipo], gf[equipo], gc[equipo], dg[equipo]])

    return ranking


if __name__ == '__main__':
    app.run(debug=True)
