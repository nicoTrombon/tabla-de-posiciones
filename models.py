from wtforms import form, fields, SelectField, DateTimeField

from flask import session, redirect, url_for

from flask_admin.form import Select2Widget
from flask_admin.contrib.pymongo import ModelView, filters
from flask_admin.model.fields import InlineFormField, InlineFieldList

import datetime



# Resultados de partidos
class ResultadoForm(form.Form):
    fecha = SelectField(label='Fecha', coerce=int, choices=[(p,p) for p in range(1,15)])

    division = SelectField(label='Division', choices=[(p.lower(), p) for p in ['Primera', 'Reserva']])
    
    equipos = choices=[(p,p) for p in [u'La Villa',
 u'Embajador',
 u'Sarmiento',
 u'Frontera',
 u'El Arenal',
 u'Chacarita',
 u'Casma',
 u'El Barrio',
 u'Defensores',
 u'Covisal',
 u'Vallejos',
 u'Belgrano',
u'Las Aguilas',
u'Las Rosas']]
    
    equipo1 = SelectField(label='Equipo 1', choices=equipos)

    goles1 = SelectField(label='Goles Equipo 1', coerce=int, choices=[(p,p) for p in range(15)])    
    
    equipo2 = fields.SelectField(label='Equipo 2', choices=equipos) 
           
    
    goles2 = SelectField(label='Goles Equipo 2', coerce=int, choices=[(p,p) for p in range(15)])

    campeonato = SelectField(label='Campeonato', coerce=int, choices=[(2017,2017),])

    tstamp = datetime.datetime.now()

    #timestamp = DateTimeField('Fecha Creacion', format="%Y-%m-%d %H:%M:%s", default=tstamp)


class ResultadoView(ModelView):
    def is_accessible(self):
        return session.get('is_admin')

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login'))

    column_list = ('campeonato', 'division', 'fecha', 'equipo1', 'goles1', 'equipo2',  'goles2', 'tstamp')
    column_sortable_list = ('campeonato', 'division', 'fecha', 'equipo1', 'equipo2', 'goles1', 'goles2', 'tstamp')

    form = ResultadoForm



