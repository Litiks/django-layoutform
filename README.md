# django-layoutform
Form templating tool for Django, which integrates a 'layout' definition to standardize the rendering of columns, groups, and form headers.

It's easy to render a simple form in django (`{{ form }}`). But what happens when you want a custom layout? Say you want some fields to be displayed across two columns, or you want formset instances to be grouped visually?

This app lets you render a form using `{{ form|layout }}`, which - when rendered - uses layout information provided within your form element to take hints on how to visually lay out the form fields. Then it renders the form using Bootstrap 3 form styling. See example in 'usage' below.

While this app isn't a perfect implementation of this approach; I think it's a great design practice to abstract the layout instructions (things like column behaviour, and visual groups) from the css/styling code that actually implements this structure. This way - when you're upgrading to the next version of bootstrap - you have ONE place to modify your styling. How wonderful!


Install
-------

- using pip: `pip install https://github.com/Litiks/django-layoutform/archive/master.zip`
- or: add to your requirements.txt: `-e git+https://github.com/Litiks/django-layoutform.git#egg=django-layoutform`
- or: copy the 'layoutform' folder to your python working directory


Integrate
---------

1. Add 'layoutform' to your settings.INSTALLED_APPS


Usage
-----

On your form, add a `field_layout` method:

```
class MyModelForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = ('first_name','last_name','gender','dob','mom_first_name','mom_last_name')

    def field_layout(self):
        """ 
            This optional method defines the field layout on the page. (Ordering, grouping, rows and columns)

            It should return:
            - a list of elements, which are either headers, rows, or group-blocks
            - each row defines a list of fields, each field is it's own column.
                - col width defines how wide each column should be. (1-12, default=12)
                - col limit (default=None) defines how many columns should be added before creating a new row div.
                    Note*: col limit does not include any special handling for hidden fields. This may be problematic for forms with a large portion of hidden/smart fields.

        """
        return [
            {'type':'header', 'name'="Personal Info", 'description':"Enter personal info"},
            {'type':'row', 'col_width':6, 'col_limit':2, 'cols':['first_name','last_name','gender','dob']},
            {'type':'group_start', 'name'="Mother", 'description':"Enter your mom's details"},
            {'type':'row', 'col_width':4, 'col_limit': 2, 'cols':['mom_first_name','mom_last_name']},
            {'type':'group_end'},
        ]
```

Then, within your template:
```
{% load layoutform %}
<form method="POST" action="." enctype="multipart/form-data">
    {% csrf_token %}
    {{ form|layout }}
    <button class="btn btn-primary" type="submit">Continue</button>
</form>
```

