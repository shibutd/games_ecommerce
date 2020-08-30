import logging
import csv
from datetime import datetime
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.http import HttpResponse
from allauth.socialaccount.models import (SocialApp, SocialAccount,
                                          SocialToken)
from .models import (CustomUser, Address, Product, ProductTag,
                     Order, OrderLine, ProductImage, Payment, Coupon)

logger = logging.getLogger(__name__)


def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = 'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)

    fields = [field for field in opts.get_fields() if not
              field.many_to_many and not field.one_to_many]
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])
    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)
    return response


export_to_csv.short_description = 'Export to CSV'


class AddressInline(admin.TabularInline):
    model = Address


class CustomerUserAdmin(DjangoUserAdmin):
    """
    Define admin model for custom User model with no username field.
    """
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    inlines = [AddressInline]


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'in_stock', 'price')
    list_filter = ('in_stock', 'date_updated')
    list_editable = ('in_stock',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('tags',)


class ProductInline(admin.TabularInline):
    model = ProductTag.product_set.through
    extra = 0


class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_filter = ('active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('product',)
    inlines = [ProductInline]


class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_tag', 'product_name')
    readonly_fields = ('thumbnail',)
    search_fields = ('product__name',)

    def thumbnail_tag(self, obj):
        """
        Return HTML for 'thumbnail_tag'.
        """
        if obj.thumbnail:
            return format_html(
                '<img src={}/>'.format(obj.thumbnail.url))
        return '-'

    thumbnail_tag.short_description = 'Thumbnail'

    def product_name(self, obj):
        return obj.product.name


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    raw_id_fields = ('product',)
    fields = ('product', 'status', 'quantity')
    readonly_fields = ('quantity',)
    can_delete = False


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'billing_address', 'shipping_address',
                    'status', 'payment')

    list_display_links = ['user', 'billing_address', 'shipping_address',
                          'payment']
    list_filter = ('status', 'shipping_address__country', 'date_added')
    search_fields = ['user__email']
    inlines = [OrderLineInline]
    actions = [export_to_csv]


class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street_address', 'apartment_address',
                    'city', 'country', 'address_type',
                    'is_default']

    list_filter = ['is_default', 'address_type', 'country']

    search_fields = ['user__email', 'street_address', 'city']


class MyAdminSite(admin.AdminSite):
    site_header = 'Games4Everyone administration'
    site_header_color = 'black'
    module_caption_color = 'grey'

    def each_context(self, request):
        context = super().each_context(request)
        context['site_header_color'] = self.site_header_color
        context['module_caption_color'] = self.module_caption_color
        return context

    def has_permission(self, request):
        return request.user.is_staff


new_admin = MyAdminSite(name='myadmin')
new_admin.register(CustomUser, CustomerUserAdmin)
new_admin.register(Product, ProductAdmin)
new_admin.register(ProductTag, ProductTagAdmin)
new_admin.register(ProductImage, ProductImageAdmin)
new_admin.register(Order, OrderAdmin)
new_admin.register(Address, AddressAdmin)
new_admin.register(Payment)
new_admin.register(Coupon)
new_admin.register(SocialApp)
new_admin.register(SocialAccount)
new_admin.register(SocialToken)
