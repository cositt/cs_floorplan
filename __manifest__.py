{
    'name': 'Centro Sanitario - Plano de Residencia',
    'version': '1.0.0',
    'category': 'Healthcare',
    'author': 'Equilibrium',
    'license': 'LGPL-3',
    'summary': 'Plano interactivo por planta: distribución de habitaciones y reubicación de residentes por arrastrar y soltar',
    'depends': ['base', 'mail', 'cs_resident'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/residence_floor_views.xml',
        'views/residence_views.xml',
        'reports/residence_floor_reports.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cs_floorplan/static/src/floorplan/floorplan_canvas.js',
            'cs_floorplan/static/src/floorplan/floorplan_canvas.xml',
            'cs_floorplan/static/src/floorplan/floorplan_canvas.scss',
        ],
    },
    'installable': True,
    'application': True,
}
