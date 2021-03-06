from django.contrib import admin
from rooibos.data.models import FieldSet
from models import Presentation, PresentationItem, PresentationItemInfo

class PresentationItem_inline(admin.StackedInline):
    model = PresentationItem
    extra = 1

class PresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'slides', 'owner', 'created', 'modified', 'hidden', 'hide_default_data')
    list_filter = ('hidden', 'hide_default_data')
    search_fields = ['title', 'name']
    ordering = ('created', 'modified')
    raw_id_fields = ('owner', )
    date_hierarchy = ('created')
    readonly_fields = ('name', 'created', 'modified')
    inlines = [
        PresentationItem_inline,
    ]

    def slides(self, obj):
        return obj.visible_item_count() + obj.hidden_item_count()


admin.site.register(Presentation, PresentationAdmin)

