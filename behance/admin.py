from django.utils.translation import ugettext as _
from django.urls import reverse
from django.http import HttpResponse
from django.conf.urls import url
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.contrib.modeladmin.helpers import AdminURLHelper, ButtonHelper
from wagtail.contrib.modeladmin.views import IndexView

from wagtailorderable.modeladmin.mixins import OrderableMixin

import requests

from .models import BehanceProject

class ImportButtonHelper(ButtonHelper):
    import_button_classnames = ['bicolor', 'icon', 'icon-download']

    def import_button(self, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        classnames = self.import_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        text = _('Import {}'.format(self.verbose_name_plural.title()))

        return {
            'url': self.url_helper.get_action_url('import', query_params=self.request.GET),
            'label': text,
            'classname': cn,
            'title': text
        }


class ImportAdminURLHelper(AdminURLHelper):
    non_object_specific_actions = ['create', 'choose_parent', 'index', 'import']

    def get_action_url(self, action, *args, **kwargs):
        query_params = kwargs.pop('query_params', None)

        url_name = self.get_action_url_name(action)
        if action in self.non_object_specific_actions:
            url = reverse(url_name)
        else:
            url = reverse(url_name, args=args, kwargs=kwargs)

        return url

    def get_action_url_pattern(self, action):
        if action in self.non_object_specific_actions:
            return self._get_action_url_pattern(action)

        return self._get_object_specific_action_url_pattern(action)


class ImportView(IndexView):
    def import_projects(self):
        
        try:
            url = 'https://api.behance.net/v2/users/AgenciaEgo/projects?client_id={}'.format(settings.BEHANCE_API_KEY)


            resp = requests.get(url)
            data = resp.json()


            for project in data.get('projects'):
                behance_id = project.get('id')
                behance_name = project.get('name')
                name = behance_name

                try:
                    db_project = BehanceProject.objects.get(behance_id=behance_id)
                    db_project.behance_name = behance_name
                except BehanceProject.DoesNotExist:
                    db_project = BehanceProject(
                        behance_id=behance_id,
                        behance_name=behance_name,
                        name=behance_name
                    )
                
                db_project.save()


            messages.add_message(self.request, messages.SUCCESS, _('Projects imported correctly'))
            return redirect('behance_behanceproject_modeladmin_index')
                
        except AttributeError:
            messages.add_message(self.request, messages.ERROR, _(
                'BEHANCE_API_KEY not set'))
            return redirect('behance_behanceproject_modeladmin_index')






    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        return self.import_projects()


class ImportModelAdminMixin(object):
    button_helper_class =ImportButtonHelper
    url_helper_class = ImportAdminURLHelper

    import_view_class = ImportView

    def get_admin_urls_for_registration(self):
        urls = super().get_admin_urls_for_registration()
        urls += (
            url(
                self.url_helper.get_action_url_pattern('import'),
                self.import_view,
                name=self.url_helper.get_action_url_name('import')
            ),
        )

        return urls

    def import_view(self, request):
        kwargs = {'model_admin': self}
        view_class = self.import_view_class
        return view_class.as_view(**kwargs)(request)

class BehanceProjectAdmin(ImportModelAdminMixin, OrderableMixin, ModelAdmin):
    model = BehanceProject
    menu_label = 'Behance Projects'
    menu_icon = 'placeholder'
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ['name',]
    search_fields = ('name',)
    ordering = ['sort_order']


modeladmin_register(BehanceProjectAdmin)
