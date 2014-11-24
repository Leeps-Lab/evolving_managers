# -*- coding: utf-8 -*-
# <standard imports>
from __future__ import division
from otree.db import models
import otree.models
from otree import widgets
import random
from otree.common import Currency as c, currency_range
# </standard imports>


doc = """
This is a 2-player 2-strategy coordination game. The original story was from <a href="https://en.wikipedia.org/wiki/Jean-Jacques_Rousseau" target="_blank">Jean-Jacques Rousseau</a>.
<br />
Source code <a href="https://github.com/oTree-org/oTree/tree/master/stag_hunt" target="_blank">here</a>.

<h3>Recommended Literature</h3>
<ul>
    <li></li>
    <li></li>
</ul>

<p>
    <strong>Wikipedia:</strong>
    <a target="_blank" href="https://en.wikipedia.org/wiki/Stag_hunt">Stag Hunt</a>,&nbsp
    <a target="_blank" href="https://en.wikipedia.org/wiki/Coordination_game">Coordination Game</a>
</p>

<p>
    <strong>Keywords:</strong>
    <a target="_blank" href="https://duckduckgo.com/?q=Stag+Hunt+game+theory&t=otree"</a>
        <span class="badge">Stag Hunt</span>
    </a>,
    <a target="_blank" href="https://duckduckgo.com/?q=coordination+game+theory&t=otree"</a>
        <span class="badge badge-info"></span>
    </a>,
    <a target="_blank" href="https://duckduckgo.com/?q=cooperation+game+theory&t=otree"</a>
        <span class="badge badge-info"></span>
    </a>,
        <a target="_blank" href="https://duckduckgo.com/?q=social+contract+game+theory&t=otree"</a>
        <span class="badge badge-info"></span>
    </a>
</p>

"""

source_code = "https://github.com/oTree-org/oTree/tree/master/stag_hunt"

recomended_lirerature = (
    (
        'Skyrms, Brian. "The stag hunt." Proceedings and Addresses of the '
        'American Philosophical Association. American Philosophical '
        'Association, 2001.'
    ),
    (
        'Battalio, Raymond, Larry Samuelson, and John Van Huyck. '
        '"Optimization incentives and coordination failure in laboratory stag '
        'hunt games."Econometrica 69.3 (2001): 749-764.'
    )
)


links = {
    "Wikipedia": {
        "Stag Hunt": "https://en.wikipedia.org/wiki/Stag_hunt",
        "Coordination Game": "https://en.wikipedia.org/wiki/Coordination_game"
    }
}

keywords = ("Stag Hunt", "Coordination", "Cooperation", "Social Contract")



class Constants:
    name_in_url = 'stag_hunt'
    players_per_group = 2
    number_of_rounds = 1

    fixed_pay = c(10)

    stag_stag_amount = c(200)
    stag_hare_amount = c(0)
    hare_stag_amount = c(100)
    hare_hare_amount = c(100)


    training_question_1_my_payoff_correct = c(0)
    training_question_1_other_payoff_correct = c(100)
    training_1_maximun_offered_points = c(200)


class Subsession(otree.models.BaseSubsession):
    pass


class Group(otree.models.BaseGroup):

    # <built-in>
    subsession = models.ForeignKey(Subsession)
    # </built-in>


class Player(otree.models.BasePlayer):

    # <built-in>
    group = models.ForeignKey(Group, null=True)
    subsession = models.ForeignKey(Subsession)
    # </built-in>

    training_question_1_my_payoff = models.CurrencyField()

    training_question_1_other_payoff = models.CurrencyField()

    decision = models.CharField(
        doc="""The player's choice""",
        widget=widgets.RadioSelect()
    )

    def is_training_question_1_my_payoff_correct(self):
        return (self.training_question_1_my_payoff==
                Constants.training_question_1_my_payoff_correct)

    def is_training_question_1_other_payoff_correct(self):
        return (self.training_question_1_other_payoff==
                Constants.training_question_1_other_payoff_correct)

    def training_question_1_my_payoff_bounds(self):
        return [0, Constants.training_1_maximun_offered_points]

    def training_question_1_other_payoff_bounds(self):
        return [0, Constants.training_1_maximun_offered_points]

    def decision_choices(self):
        return ['Stag', 'Hare']

    def other_player(self):
        """Returns other player in group"""
        return self.get_others_in_group()[0]

    def set_payoff(self):

        payoff_matrix = {
            'Stag': {
                'Stag': Constants.stag_stag_amount,
                'Hare': Constants.stag_hare_amount,
            },
            'Hare': {
                'Stag': Constants.hare_stag_amount,
                'Hare': Constants.hare_hare_amount,
            }
        }
        self.payoff = payoff_matrix[self.decision][self.other_player().decision]


