from django import forms


class SuggestWidget(forms.Select):
    template_name = 'ptop/widgets/suggest.html'

    class Media:
        js = ['ptop/js/suggest.js']
        css = {
            'all': ['ptop/css/suggest.css']
        }

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if 'class' in self.attrs:
            self.attrs['class'] += ' suggest'
        else:
            self.attrs['class'] = 'suggest'
