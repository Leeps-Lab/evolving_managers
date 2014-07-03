# -*- coding: utf-8 -*-
import bargaining.models as models
from bargaining.utilities import ParticipantMixin
import ptree.forms


class RequestForm(ParticipantMixin, ptree.forms.Form):

    class Meta:
        model = models.Participant
        fields = ['request_amount']

    def labels(self):
        return {'request_amount': 'Make your request?'}

    def choices(self):
        return {'request_amount': self.match.get_request_field_choices()}
