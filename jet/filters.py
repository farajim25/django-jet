from django.contrib.admin import RelatedFieldListFilter, FieldListFilter
from django.utils.encoding import smart_text
from django.utils.html import format_html
from django.utils.translation import ugettext as _

try:
    from django.core.urlresolvers import reverse
except ImportError: # Django 1.11
    from django.urls import reverse

try:
    from django.contrib.admin.utils import get_model_from_relation
except ImportError: # Django 1.6
    from django.contrib.admin.util import get_model_from_relation

try:
    from django.forms.utils import flatatt
except ImportError: # Django 1.6
    from django.forms.util import flatatt


class RelatedFieldAjaxListFilter(RelatedFieldListFilter):
    template = 'jet/related_field_ajax_list_filter.html'
    ajax_attrs = None

    def has_output(self):
        return True

    def field_choices(self, field, request, model_admin):
        model = field.remote_field.model if hasattr(field, 'remote_field') else field.related_field.model
        app_label = model._meta.app_label
        model_name = model._meta.object_name

        self.ajax_attrs = format_html('{0}', flatatt({
            'data-app-label': app_label,
            'data-model': model_name,
            'data-ajax--url': reverse('jet:model_lookup'),
            'data-queryset--lookup': self.lookup_kwarg
        }))

        if self.lookup_val is None:
            return []

        other_model = get_model_from_relation(field)
        if hasattr(field, 'rel'):
            rel_name = field.rel.get_related_field().name
        else:
            rel_name = other_model._meta.pk.name

        queryset = model._default_manager.filter(**{rel_name: self.lookup_val}).all()
        return [(x._get_pk_val(), smart_text(x)) for x in queryset]


try:
    from collections import OrderedDict
    from django import forms
    from django.contrib.admin.widgets import AdminDateWidget, AdminSplitDateTime
    from rangefilter.filter import DateRangeFilter as OriginalDateRangeFilter
    from rangefilter.filter import DateTimeRangeFilter as OriginalDateTimeRangeFilter


    class DateRangeFilter(OriginalDateRangeFilter):
        def get_template(self):
            return 'rangefilter/date_filter.html'

        def _get_form_fields(self):
            # this is here, because in parent DateRangeFilter AdminDateWidget
            # could be imported from django-suit
            return OrderedDict((
                (self.lookup_kwarg_gte, forms.DateField(
                    label='',
                    widget=AdminDateWidget(attrs={'placeholder': _('From date')}),
                    localize=True,
                    required=False
                )),
                (self.lookup_kwarg_lte, forms.DateField(
                    label='',
                    widget=AdminDateWidget(attrs={'placeholder': _('To date')}),
                    localize=True,
                    required=False
                )),
            ))

        @staticmethod
        def _get_media():
            css = [
                'style.css',
            ]
            return forms.Media(
                css={'all': ['range_filter/css/%s' % path for path in css]}
            )


    class DateTimeRangeFilter(OriginalDateTimeRangeFilter):
        def get_template(self):
            return 'rangefilter/date_filter.html'

        def _get_form_fields(self):
            return OrderedDict(
                (
                    (self.lookup_kwarg_gte, forms.SplitDateTimeField(
                        label='',
                        widget=AdminSplitDateTime(attrs={'placeholder': _('From date'), 'autocomplete': 'off'}),
                        localize=True,
                        required=False
                    )),
                    (self.lookup_kwarg_lte, forms.SplitDateTimeField(
                        label='',
                        widget=AdminSplitDateTime(attrs={'placeholder': _('To date'), 'autocomplete': 'off'}),
                        localize=True,
                        required=False
                    )),
                )
            )

        @staticmethod
        def _get_media():
            css = [
                'style.css',
            ]
            return forms.Media(
                css={'all': ['range_filter/css/%s' % path for path in css]}
            )

except ImportError:
    pass

try:
    from django.templatetags.static import StaticNode
    from rangefilter_jalali.filter import jDateRangeFilter as OriginaljDateRangeFilter
    from rangefilter_jalali.filter import jDateTimeRangeFilter as OriginaljDateTimeRangeFilter
    from rangefilter_jalali.filter import DateRangeFilter as OriginalGDateRangeFilter
    from rangefilter_jalali.filter import DateTimeRangeFilter as OriginalGDateTimeRangeFilter

    class JalaliRangeFilterMixin:
        def get_template(self):
            return 'rangefilter/date_filter.html'

        @staticmethod
        def get_js():
            return [
                StaticNode.handle_simple('admin/js/calendar.js'),
                StaticNode.handle_simple('admin/js/admin/DateTimeShortcuts.js'),
            ]

        @staticmethod
        def _get_media():
            js = [
                'admin/js/calendar.js',
                'admin/js/admin/DateTimeShortcuts.js',
                'admin/jquery.ui.datepicker.jalali/scripts/jquery-1.10.2.min.js',
                'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.core.js',
                'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc.js',
                'admin/jquery.ui.datepicker.jalali/scripts/calendar.js',
                'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc-fa.js',
                'admin/main.js',
            ]
            css = [
                'widgets.css',
                'main.css',
            ]
            jet_css = [
                'style.css',
                'jalali.css'
            ]
            return forms.Media(
                js=['%s' % url for url in js],
                css={'all': ['admin/css/%s' % path for path in css] + ['range_filter/css/%s' % path for path in jet_css]}
            )

    class GDateRangeFilter(JalaliRangeFilterMixin, OriginalGDateRangeFilter):
        pass

    class GDatetimeRangeFilter(JalaliRangeFilterMixin, OriginalGDateTimeRangeFilter):
        pass

    class JDateRangeFilter(JalaliRangeFilterMixin, OriginaljDateRangeFilter):
        pass

    class JDatetimeRangeFilter(JalaliRangeFilterMixin, OriginaljDateTimeRangeFilter):
        pass

except ImportError:
    pass


class InputFilter(FieldListFilter):
    template = 'jet-filters/inputfilter/input_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.parameter_name = field.name
        super().__init__(field, request, params, model, model_admin, field_path)

    def lookups(self, request, model_admin):
        return ((),)

    def value(self):
        return self.used_parameters.get(self.parameter_name)

    def choices(self, changelist):
        query_parts = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield {
            'empty': self.value() is None,
            'query_parts': query_parts,
            'query_string': changelist.get_query_string(remove=[self.parameter_name]),
        }

    def expected_parameters(self):
        return [self.parameter_name]
