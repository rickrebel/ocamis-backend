from django.contrib import admin

from intl_medicine.models import PrioritizedComponent, Respondent, GroupAnswer


class PrioritizedComponentAdmin(admin.ModelAdmin):
    list_display = (
        'component',
        'group_answer',
        'is_prioritized',
        'is_low_priority',
    )
    list_filter = (
        'group_answer__group',
        'group_answer__respondent',
    )
    search_fields = ('component__name',)
    raw_id_fields = ('component', 'group_answer')


class PrioritizedComponentInline(admin.TabularInline):
    model = PrioritizedComponent
    extra = 0
    fields = ('component', 'is_prioritized', 'is_low_priority')
    raw_id_fields = ('component',)


class GroupAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'group',
        'respondent',
        'date_started',
        'date_finished',
    )
    list_filter = ('group', 'respondent', 'group__need_survey')
    raw_id_fields = ('group', 'respondent')
    inlines = [PrioritizedComponentInline]


class GroupAnswerInline(admin.TabularInline):
    model = GroupAnswer
    extra = 0
    fields = ('group', 'date_started', 'date_finished')
    readonly_fields = ('date_started', 'date_finished')
    raw_id_fields = ('group',)
    show_change_link = True


class RespondentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'first_name',
        'last_name',
        'email',
        'institution',
        'position',
        'recognition',
    )
    list_filter = ['recognition']
    inlines = [GroupAnswerInline]


admin.site.register(PrioritizedComponent, PrioritizedComponentAdmin)
admin.site.register(GroupAnswer, GroupAnswerAdmin)
admin.site.register(Respondent, RespondentAdmin)
