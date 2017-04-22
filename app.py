from collections import Counter, defaultdict

from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_cache import Cache
from flask_admin import Admin

from pymongo import MongoClient
import datetime

from models import ResultadoView
from db_config import uri
from db_admin import is_valid
from settings import DIVISIONES

app = Flask(__name__)
admin = Admin(app)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

#necessary for sessions
app.config['SECRET_KEY'] = '123456790'

db = MongoClient(uri, connect=False).futbol_sma

admin.add_view(ResultadoView(db.resultados, 'Resultado'))

TORNEO = sorted(db.resultados.distinct('campeonato'))[-1]

update_now = False


def set_update_true():
    global update_now
    update_now = True

def recalculate():
    return update_now

@app.route('/', methods=['GET'])
@app.route('/tabla', methods=['GET'])
def main():

    division = request.args.get('division')
    if division not in DIVISIONES:
        division = 'primera'

    titulos = ['Posicion', 'Equipo', 'Puntos', 'PJ', 'PG', 'PE', 'PP', 'GF', 'GE', 'DG']
    tabla = get_posiciones(division)

    return render_template('tabla.html', rank=tabla, rank_head=titulos,
                           division=division.capitalize(), divisiones=DIVISIONES)



@app.route('/resultados', methods=['GET'])
def resultados():
    division = request.args.get('division')

    if division not in DIVISIONES:
        division = 'primera'

    fechas = get_fechas(division)

    resultados = get_resultados(division)

    return render_template('resultados.html', fechas=fechas, resultados=resultados,
                           division=division.capitalize(), divisiones=DIVISIONES)


@app.route('/admininstrador', methods=['GET'])
def administrador():
    return render_template('admin.html', login=session.get('is_admin'))


@app.route('/login', methods=['POST'])
def login():
    error = None

    if request.method == 'POST':
        if not is_valid(request.form['uname'], request.form['psw']):
            error = 'Invalid credentials'
        else:
            flash('You were successfully logged in')
            session['is_admin'] = True
            return redirect(url_for('administrador'))


@app.route('/logout', methods=['GET','POST'])
def destroy_session():
    session.clear()
    return redirect(url_for('main'))


@cache.memoize(unless=recalculate)
def get_posiciones(division='primera', year=2017):
    for doc in db.posiciones.find({'division': division, 'posiciones': {'$nin': [None, []]}}).sort('tstamp', -1):
        tabla = doc['posiciones']
        return tabla


@app.route('/actualizo', methods=['GET'])
def actualizo():

    if not session.get('is_admin'):
        return 'Unauthorized', 404

    year = sorted(db.resultados.distinct('campeonato'))[-1]

    for division in ['primera', 'reserva']:
        res = calcular_posiciones(division=division, year=year)
        tstamp = datetime.datetime.now()
        db.posiciones.insert({'division': division, 'tstamp': tstamp, 'posiciones': res})

    set_update_true()

    for division in ['primera', 'reserva']:
        get_posiciones(division)

    return redirect(url_for('main'))



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

    sorter = Counter()  # tengo que poder diferenciar ranking de equipos de igual puntaje
    for equipo in puntos:
        sorter[equipo] = sorter[equipo] = 1000 * puntos[equipo] + 10 * dg[equipo] + gf[equipo]

    rank = 0
    for equipo, _ in sorter.most_common():
        rank += 1
        ranking.append([rank, equipo, puntos[equipo], pj[equipo], pg[equipo], pe[equipo], pp[equipo], gf[equipo], gc[equipo], dg[equipo]])

    return ranking


@cache.memoize(1000)
def get_fechas(division='primera'):
    return sorted(db.resultados.find({'campeonato': TORNEO, 'division': division}).distinct('fecha'), reverse=True)


@cache.memoize(1000)
def get_resultados(division='primera'):
    resultados = defaultdict(list)

    for doc in db.resultados.find({'campeonato': TORNEO, 'division': division}):
        resultados[doc['fecha']].append({'e1': doc['equipo1'].upper(), 'g1': doc['goles1'],
                                         'e2': doc['equipo2'].upper(), 'g2': doc['goles2']})
    return resultados




#if __name__ == '__main__':
#    app.run(debug=True)
