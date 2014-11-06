# -*- coding: utf-8 -*-
# <standard imports>
from __future__ import division
from otree.db import models
import otree.models
from otree import widgets
from otree.common import Currency as c, currency_range
import random
# </standard imports>


doc = """
This is a standard 2-player trust game where the amount sent by player 1 gets tripled. 
The trust game was first proposed by <a href="http://econweb.ucsd.edu/~jandreon/Econ264/papers/Berg%20et%20al%20GEB%201995.pdf" target="_blank">Berg, Dickhaut, and McCabe (1995)</a>.
<br />
Source code <a href="https://github.com/oTree-org/oTree/tree/master/trust"
target="_blank">here</a>.
"""

class Constants:
    name_in_url = 'trust'
    players_per_group = 2
    number_of_rounds = 1

    #Initial amount allocated to each player
    amount_allocated = c(100)
    multiplication_factor = 3
    bonus = c(10)


class Subsession(otree.models.BaseSubsession):

    pass



class Group(otree.models.BaseGroup):


    # <built-in>
    subsession = models.ForeignKey(Subsession)
    # </built-in>

    sent_amount = models.CurrencyField(
        doc="""Amount sent by P1""",
    )

    sent_back_amount = models.CurrencyField(
        doc="""Amount sent back by P2""",
    )

    def set_payoffs(self):
        p1 = self.get_player_by_id(1)
        p2 = self.get_player_by_id(2)
        p1.payoff = Constants.bonus + Constants.amount_allocated\
            - self.sent_amount + self.sent_back_amount
        p2.payoff = Constants.bonus + self.sent_amount * Constants.multiplication_factor - self.sent_back_amount

    def sent_amount_error_message(self, value):
        if not 0 <= value <= Constants.amount_allocated:
            return 'Your entry is invalid.'

    def sent_back_amount_error_message(self, value):
        if not 0 <= value <= self.sent_amount * Constants.multiplication_factor:
            return 'Your entry is invalid.'


class Player(otree.models.BasePlayer):

    # <built-in>
    group = models.ForeignKey(Group, null=True)
    subsession = models.ForeignKey(Subsession)
    # </built-in>
    training_answer_x = models.CurrencyField(
        null=True, verbose_name='Participant A would have')
    training_answer_y = models.CurrencyField(
        null=True, verbose_name='Participant B would have')

    def role(self):
        return {1: 'A', 2: 'B'}[self.id_in_group]
