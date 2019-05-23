import os
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
import re
import sys

from .models import BehanceProject, BehanceProjectModule
from .helpers import create_wagtail_image_from_remote

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
        images_folder = 'original_images'

        try:
            url = 'https://api.behance.net/v2/users/AgenciaEgo/projects?client_id={}'.format(settings.BEHANCE_API_KEY)


            resp = requests.get(url)
            data = resp.json()


            for project in data.get('projects'):
                is_project_new = False
                behance_id = project.get('id')
                behance_name = project.get('name')
                name = behance_name
                cover_url = project.get('covers').get('original')

                try:
                    db_project = BehanceProject.objects.get(behance_id=behance_id)
                    db_project.behance_name = behance_name
                except BehanceProject.DoesNotExist:
                    is_project_new = True
                    db_project = BehanceProject(
                        behance_id=behance_id,
                        behance_name=behance_name,
                        name=behance_name,
                        cover=create_wagtail_image_from_remote(cover_url),
                    )
                
                db_project.save()

                # get project details and modules
                project_url = 'https://www.behance.net/v2/projects/{}?api_key={}'.format(db_project.behance_id, settings.BEHANCE_API_KEY)

                print('fetching {}'.format(project_url))

                resp = requests.get(project_url)
                data = resp.json()
                project_item = data.get('project')

                print(project_item.get('name'))
                
                # save description on first save
                if is_project_new:
                    db_project.description = project.get('description')
                    db_project.save()

                # clear all modules
                db_project.modules.all().delete()
                sort_order = 1
                for module in project_item.get('modules'):
                    if module.get('type') == 'image':
                        image = create_wagtail_image_from_remote(module.get('sizes').get('original'))
                        text = None
                    elif module.get('type') == 'text':
                        image = None
                        regex = r"</?span( style=\"[\Wa-z0-9#:;]*\\?\")?>"
                        test_str = module.get('text')
                        subst = ""
                        # You can manually specify the number of replacements by changing the 4th argument
                        text = re.sub(regex, subst, test_str, 0, re.MULTILINE | re.IGNORECASE)
                    else:
                        image = None
                        text = None

                    db_module = BehanceProjectModule(
                        sort_order=sort_order,
                        type=module.get('type'),
                        image=image,
                        text=text,
                        project=db_project
                    )
                    db_module.save()
                    sort_order += 1



            messages.add_message(self.request, messages.SUCCESS, _('Projects imported correctly'))
            return redirect('behance_behanceproject_modeladmin_index')
                
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            
            messages.add_message(self.request, messages.ERROR, '{} on {} on line {}'.format('Exception', fname, exc_tb.tb_lineno))
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
