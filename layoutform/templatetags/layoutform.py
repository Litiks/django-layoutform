from django.template import Context
from django.template.loader import get_template
from django import template
from django.utils.safestring import mark_safe
from django import forms

register = template.Library()

def is_checkbox(widget):
    return isinstance(widget, forms.CheckboxInput)

def is_multiple_checkbox(widget):
    return isinstance(widget, forms.CheckboxSelectMultiple)

def is_radio(widget):
    return isinstance(widget, forms.RadioSelect)

def is_file(widget):
    return isinstance(widget, forms.FileInput)

@register.filter
def layout(obj):
    """ Turns out, using templates is a bit slow when you need to do things hundreds of times. 
        So; we generate html code here. Easy peasy.
    """
    obj_type = obj.__class__.__name__.lower()
    if obj_type == 'boundfield':
        # template = get_template("bootstrapform/field.html")
        # context = Context({'field': obj, 'form': obj.form})
        # return template.render(context)

        field = obj
        form = field.form
        widget = field.field.widget
        rows = []
        required_css_class = getattr(form,'required_css_class','required')
        error_css_class = getattr(form,'error_css_class','')

        err_class = ''
        if field.errors:
            err_class = 'has-error'
        rows.append(u"<div class='form-group %s'>" % err_class)

        if is_checkbox(widget):
            rows.append("<div>")
            rows.append("<div class='checkbox'>")
            if field.auto_id:
                req_class = ''
                if field.field.required:
                    req_class = required_css_class
                rows.append(u"<label class='%s'>%s <span>%s</span></label>" % (req_class, field, field.label))

            for error in field.errors:
                rows.append(u"<span class='help-block %s'>%s</span>" % (error_css_class, error))
            if field.help_text:
                rows.append(u"<p class='help-block'>%s</p>" % field.help_text)

            rows.append("</div>")
            rows.append("</div>")

        elif is_radio(widget):
            if field.auto_id:
                req_class = ''
                if field.field.required:
                    req_class = required_css_class
                rows.append(u"<label class='control-label %s'>%s</label>" % (req_class, field.label))

            rows.append("<div>")
            for choice in field:
                rows.append(u"<div class='radio'><label>%s %s</label></div>" % (choice.tag, choice.choice_label))

            for error in field.errors:
                rows.append(u"<span class='help-block %s'>%s</span>" % (error_css_class, error))
            if field.help_text:
                rows.append(u"<p class='help-block'>%s</p>" % field.help_text)

            rows.append("</div>")

        else:
            if field.auto_id:
                req_class = ''
                if field.field.required:
                    req_class = required_css_class
                rows.append(u"<label class='control-label %s' for='%s'>%s</label>" % (req_class, field.auto_id, field.label))

            mult_class = ''
            if is_multiple_checkbox(widget):
                mult_class = 'multiple-checkbox'
            elif not is_file(widget):
                # replaces add_input_classes
                field_classes = widget.attrs.get('class', '')
                field_classes += ' form-control'
                field.field.widget.attrs['class'] = field_classes

            rows.append(u"<div class='%s'>" % mult_class)
            rows.append(unicode(field))

            for error in field.errors:
                rows.append(u"<span class='help-block %s'>%s</span>" % (error_css_class, error))

            if field.help_text:
                rows.append(u"<p class='help-block'>%s</p>" % field.help_text)

            rows.append("</div>")

        rows.append("</div>")
        return mark_safe("\n".join(rows))

    elif hasattr(obj, 'management_form'):
        # it's a formset
        template = get_template("layoutform/formset.html")
        context = Context({'formset': obj})
        return template.render(context)

    else:
        # it's a form.
        form = obj
        rows = []

        # errors
        if form.errors:
            e = ""
            if len(form.errors) > 1:
                e = "s"
            rows.append(u"<div class='alert alert-danger'><a class='close' data-dismiss='alert'>&times;</a> Please correct the error%s below.</div>" % e)

        errors = form.non_field_errors()
        if errors:
            rows.append("<div class='alert alert-danger'><a class='close' data-dismiss='alert'>&times;</a>")
            for e in errors:
                rows.append(u"%s" % e)
            rows.append("</div>")

        # hidden fields
        for field in form.hidden_fields():
            rows.append(unicode(field))

        try:
            field_layout = getattr(form, 'field_layout', None)()
        except TypeError:
            field_layout = None
        if field_layout:
            for chunk in field_layout:
                chunk_type = chunk['type']
                name = chunk.get('name')
                description = chunk.get('description')

                if chunk_type == 'header':
                    if name:
                        rows.append(u"<h3>%s</h3>" % name)
                    if description:
                        rows.append(u"<p>%s</p>" % description)

                elif chunk_type == 'group_start':
                    rows.append("<div class='well'>")
                    if name:
                        rows.append(u"<h4>%s</h4>" % name)
                    if description:
                        rows.append(u"<p>%s</p>" % description)

                elif chunk_type == 'group_end':
                    rows.append("</div>")

                elif chunk['type'] == 'row':
                    rows.append("<div class='row'>")
                    for i, col in enumerate(chunk['cols']):
                        # field = form.get(col)
                        # we can't do .get() here, because form isn't actually a dict
                        try:
                            field = form[col]
                        except KeyError:
                            field = None

                        if field and not field.is_hidden:
                            rows.append(u"<div class='col-sm-%s'>" % chunk['col_width'])
                            rows.append(u"%s" % layout(field))
                            rows.append("</div>")

                        if (i+1) % chunk.get('col_limit',1000) == 0:
                            rows.append("</div>")
                            rows.append("<div class='row'>")

                    rows.append("</div>")

        else:
            for field in form.visible_fields():
                rows.append(layout(field))

        return mark_safe("\n".join(rows))

@register.filter
def print_layout(obj):
    """ This method is the same as layout, but it displays a condenced, read-only version of the form.
        Additionally, it checks the form for 'printed_fields', in case there are additional limits applied when printing
    """
    obj_type = obj.__class__.__name__.lower()
    if obj_type == 'boundfield':
        # template = get_template("bootstrapform/field.html")
        # context = Context({'field': obj, 'form': obj.form})
        # return template.render(context)

        field = obj
        form = field.form
        widget = field.field.widget
        rows = []
        required_css_class = getattr(form,'required_css_class','required')
        error_css_class = getattr(form,'error_css_class','')

        err_class = ''
        if field.errors:
            err_class = 'has-error'
        rows.append(u"<div class='form-group %s' style='page-break-inside:avoid;'>" % err_class)

        if is_checkbox(widget):
            rows.append("<div>")
            rows.append("<div class='checkbox'>")
            if field.auto_id:
                req_class = ''
                if field.field.required:
                    req_class = required_css_class
                rows.append(u"<label class='%s'>%s <span>%s</span></label>" % (req_class, field, field.label))

            for error in field.errors:
                rows.append(u"<span class='help-block %s'>%s</span>" % (error_css_class, error))
            if field.help_text:
                rows.append(u"<p class='help-block'>%s</p>" % field.help_text)

            rows.append("</div>")
            rows.append("</div>")

        elif is_radio(widget):
            if field.auto_id:
                req_class = ''
                if field.field.required:
                    req_class = required_css_class
                rows.append(u"<label class='control-label %s'>%s</label>" % (req_class, field.label))

            rows.append("<div>")
            for choice in field:
                rows.append(u"<div class='radio'><label>%s %s</label></div>" % (choice.tag, choice.choice_label))

            for error in field.errors:
                rows.append(u"<span class='help-block %s'>%s</span>" % (error_css_class, error))
            if field.help_text:
                rows.append(u"<p class='help-block'>%s</p>" % field.help_text)

            rows.append("</div>")

        else:
            if field.auto_id:
                req_class = ''
                if field.field.required:
                    req_class = required_css_class
                rows.append(u"<label class='control-label %s' for='%s'>%s</label>" % (req_class, field.auto_id, field.label))

            mult_class = ''
            if is_multiple_checkbox(widget):
                mult_class = 'multiple-checkbox'
            elif not is_file(widget):
                # replaces add_input_classes
                field_classes = widget.attrs.get('class', '')
                field_classes += ' form-control'
                field.field.widget.attrs['class'] = field_classes

            rows.append(u"<div class='%s'>" % mult_class)
            rows.append(unicode(field))
            # rows.append(unicode(field.value()))

            for error in field.errors:
                rows.append(u"<span class='help-block %s'>%s</span>" % (error_css_class, error))

            if field.help_text:
                rows.append(u"<p class='help-block'>%s</p>" % field.help_text)

            rows.append("</div>")

        rows.append("</div>")
        return mark_safe("\n".join(rows))

    elif hasattr(obj, 'management_form'):
        # it's a formset
        template = get_template("layoutform/print_formset.html")
        context = Context({'formset': obj})
        return template.render(context)

    else:
        # it's a form.
        form = obj
        rows = []

        # errors
        if form.errors:
            e = ""
            if len(form.errors) > 1:
                e = "s"
            rows.append(u"<div class='alert alert-danger'><a class='close' data-dismiss='alert'>&times;</a> Please correct the error%s below.</div>" % e)

        errors = form.non_field_errors()
        if errors:
            rows.append("<div class='alert alert-danger'><a class='close' data-dismiss='alert'>&times;</a>")
            for e in errors:
                rows.append(u"%s" % e)
            rows.append("</div>")

        # hidden fields
        for field in form.hidden_fields():
            rows.append(unicode(field))

        try:
            field_layout = getattr(form, 'field_layout', None)()
        except TypeError:
            field_layout = None

        try:
            printed_fields = getattr(form, 'printed_fields', None)()
        except TypeError:
            printed_fields = None

        if field_layout:
            for chunk in field_layout:
                chunk_type = chunk['type']
                name = chunk.get('name')
                description = chunk.get('description')

                if chunk_type == 'header':
                    if name:
                        rows.append(u"<h3>%s</h3>" % name)
                    if description:
                        rows.append(u"<p>%s</p>" % description)

                elif chunk_type == 'group_start':
                    rows.append("<div class='well'>")
                    if name:
                        rows.append(u"<h4>%s</h4>" % name)
                    if description:
                        rows.append(u"<p>%s</p>" % description)

                elif chunk_type == 'group_end':
                    rows.append("</div>")

                elif chunk['type'] == 'row':
                    rows.append("<div class='row'>")
                    for i, col in enumerate(chunk['cols']):
                        if printed_fields is not None and col not in printed_fields:
                            continue

                        # field = form.get(col)
                        # we can't do .get() here, because form isn't actually a dict
                        try:
                            field = form[col]
                        except KeyError:
                            field = None

                        if field and not field.is_hidden:
                            rows.append(u"<div class='col-sm-%s'>" % chunk['col_width'])
                            rows.append(u"%s" % print_layout(field))
                            rows.append("</div>")

                        if (i+1) % chunk.get('col_limit',1000) == 0:
                            rows.append("</div>")
                            rows.append("<div class='row'>")

                    rows.append("</div>")

        else:
            for field in form.visible_fields():
                rows.append(print_layout(field))

        return mark_safe("\n".join(rows))

@register.filter
def extras_hidden(formset, number=1):
    forms = []
    remaining = number
    for f in formset:
        if f.initial:
            forms.append(f)
        elif f.has_changed():
            forms.append(f)
        elif remaining:
            forms.append(f)
            remaining -= 1
        # the unspoken else here, is that we don't include this form.
        # we don't break, because we don't want to miss any forms with data set
    return forms

@register.filter
def all_extras_hidden(formset, number=0):
    return extras_hidden(formset, number)
