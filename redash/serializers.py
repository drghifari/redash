"""
This will eventually replace all the `to_dict` methods of the different model classes we have. This will ensure cleaner
code and better separation of concerns.
"""

import json
from funcy import project
from redash import models, settings


def public_widget(widget):
    res = {
        'id': widget.id,
        'width': widget.width,
        'options': json.loads(widget.options),
        'text': widget.text,
        'updated_at': widget.updated_at,
        'created_at': widget.created_at
    }

    if widget.visualization and widget.visualization.id:
        query_data = models.QueryResult.query.get(widget.visualization.query_rel.latest_query_data_id).to_dict()
        res['visualization'] = {
            'type': widget.visualization.type,
            'name': widget.visualization.name,
            'description': widget.visualization.description,
            'options': json.loads(widget.visualization.options),
            'updated_at': widget.visualization.updated_at,
            'created_at': widget.visualization.created_at,
            'query': {
                'query': ' ',  # workaround, as otherwise the query data won't be loaded.
                'name': widget.visualization.query_rel.name,
                'description': widget.visualization.query_rel.description,
                'options': {},
                'latest_query_data': query_data
            }
        }

    return res


def public_dashboard(dashboard):
    if settings.ALLOW_PARAMETERS_IN_PUBLIC_DASHBOARD:
        layout = json.loads(dashboard.layout)
        widget_list = models.Widget.query.filter(
            models.Widget.dashboard == dashboard)

        widgets = {}

        for w in widget_list:
            widgets[w.id] = w.to_dict()

        widgets_layout = []
        for row in layout:
            if not row:
                continue
            new_row = []
            for widget_id in row:
                widget = widgets.get(widget_id, None)
                if widget:
                    new_row.append(widget)

            widgets_layout.append(new_row)

        dashboard_dict = {
            'id': dashboard.id,
            'slug': dashboard.slug,
            'name': dashboard.name,
            'user_id': dashboard.user_id,
            'layout': layout,
            'dashboard_filters_enabled': dashboard.dashboard_filters_enabled,
            'widgets': widgets_layout,
            'is_archived': dashboard.is_archived,
            'is_draft': dashboard.is_draft,
            'updated_at': dashboard.updated_at,
            'created_at': dashboard.created_at,
            'version': dashboard.version
        }
    else:
        dashboard_dict = project(dashboard.to_dict(), (
            'name', 'layout', 'dashboard_filters_enabled', 'updated_at',
            'created_at'))

        widget_list = (models.Widget.query
                       .filter(models.Widget.dashboard_id == dashboard.id)
                       .outerjoin(models.Visualization)
                       .outerjoin(models.Query))

        widgets = {w.id: public_widget(w) for w in widget_list}

        widgets_layout = []
        for row in dashboard_dict['layout']:
            new_row = []
            for widget_id in row:
                widget = widgets.get(widget_id, None)
                if widget:
                    new_row.append(widget)
            widgets_layout.append(new_row)

        dashboard_dict['widgets'] = widgets_layout

    return dashboard_dict
