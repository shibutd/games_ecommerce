from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from . import models


class AddressInline(admin.TabularInline):
    model = models.Address


class CustomerUserAdmin(DjangoUserAdmin):
    """
    Define admin model for custom User model with no username field.
    """
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {
            "fields": ("first_name", "last_name")
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {
            "fields": ("last_login", "date_joined")
        }),
    )
    add_fieldsets = (
        (None, {
            "fields": ("email", "password1", "password2"),
        }),
    )
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    inlines = [AddressInline]


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'in_stock', 'price')
    list_filter = ('active', 'in_stock', 'date_updated')
    list_editable = ('in_stock',)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ('tags',)


class ProductInline(admin.TabularInline):
    model = models.ProductTag.product_set.through


class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_filter = ('active',)
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
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
        return "-"

    # Defines the column name for the list_display
    thumbnail_tag.short_description = "Thumbnail"

    def product_name(self, obj):
        return obj.product.name


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'billing_address',
                    'shipping_address', 'payment']

    list_display_links = ['user', 'billing_address', 'shipping_address',
                          'payment']

    list_filter = ['status']

    search_fields = ['user__email']


class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street_address', 'apartment_address',
                    'zip_code', 'city', 'country', 'address_type',
                    'is_default']

    list_filter = ['is_default', 'address_type', 'country']

    search_fields = ['user__email', 'street_address', 'city']


admin.site.register(models.CustomUser, CustomerUserAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.ProductTag, ProductTagAdmin)
admin.site.register(models.ProductImage, ProductImageAdmin)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.Address, AddressAdmin)
admin.site.register(models.Payment)
admin.site.register(models.Coupon)
