# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from jsonfield import JSONField
from otree.api import models
from otree.constants import BaseConstants
from otree.models import BaseSubsession, BasePlayer
from otree_redwood.models import Event, DecisionGroup
from otree_redwood.utils import DiscreteEventEmitter
import csv
import random

doc = """
This is a Prisoner's Dilemna game with discrete time. Players are given two choices,
'Cooperate' or 'Don't Cooperate. Choices are distributed every N seconds, so players have
a "sub-period" of time to digest the results and strategize.
"""


class Constants(BaseConstants):
    name_in_url = 'imperfect_monitoring'
    players_per_group = 2
    num_rounds = 10

    # treatments = {
    #     'A': {
    #         'payoff_matrix': [
    #             [[100, 100], [0, 0]],
    #             [[125, 125], [25, 25]],
    #         ],
    #         'probability_matrix': [
    #             [[0.4, 0.4], [0.6, 0.6]],
    #             [[0.6, 0.6], [0.8, 0.8]],
    #         ],
    #         #[round(max(3, numpy.random.exponential(20))) for i in range(10)] 
    #         'num_subperiods': [
    #             7,
    #             3,
    #             29,
    #             11,
    #             9,
    #             6,
    #             6,
    #             3,
    #             6,
    #             13,
    #         ]
    #     }
    # }


def parse_config(config_file):
    with open('imperfect_monitoring/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'displayed_subperiods': int(row['displayed_subperiods']),
            'subperiod_length': int(row['subperiod_length']),
            'rest_length': int(row['rest_length']),
            'seconds_per_tick': int(row['seconds_per_tick']),
            'display_average_a_graph': True if row['display_average_a_graph'] == 'TRUE' else False,
            'display_average_b_graph': True if row['display_average_b_graph'] == 'TRUE' else False,
            'display_average_ab_graph': True if row['display_average_ab_graph'] == 'TRUE' else False,
            #'period_length': int(row['period_length']),
            'num_subperiods': int(row['num_subperiods']),
            'payoff_matrix': [
                [float(row['pi1(AGood)']), float(row['pi2(AGood)'])], [float(row['pi1(ABad)']), float(row['pi2(ABad)'])],
                [float(row['pi1(BGood)']), float(row['pi2(BGood)'])], [float(row['pi1(BBad)']), float(row['pi2(BBad)'])]
            ],
            'probability_matrix': [
                [float(row['p1(AA)']), float(row['p2(AA)'])], [float(row['p1(AB)']), float(row['p2(AB)'])],
                [float(row['p1(BA)']), float(row['p2(BA)'])], [float(row['p1(BB)']), float(row['p2(BB)'])]
            ],
        })
    return rounds

class Subsession(BaseSubsession):
    def before_session_starts(self):
        config = parse_config(self.session.config['config_file'])
        self.group_randomly()
        # if self.round_number > len(config):
        #     self.group_randomly()
        # elif config[self.round_number-1]['shuffle_role']:
        #     self.group_randomly()
        # else:
        #     self.group_randomly(fixed_id_in_group=True)


class Group(DecisionGroup):

    state = models.CharField(max_length=10)
    t = models.PositiveIntegerField()
    total_payoffs = JSONField()
    countGood = JSONField()
    periodResult = JSONField()
    fixed_group_decisions = JSONField()

    def subperiod_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['subperiod_length']

    def displayed_subperiods(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['displayed_subperiods']

    def display_average_a_graph(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['display_average_a_graph']

    def display_average_b_graph(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['display_average_b_graph']

    def display_average_ab_graph(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['display_average_ab_graph']

    def period_length(self):
        num_subperiods = parse_config(self.session.config['config_file'])[self.round_number-1]['num_subperiods']
        rest_length = parse_config(self.session.config['config_file'])[self.round_number-1]['rest_length']
        subperiod_length = parse_config(self.session.config['config_file'])[self.round_number-1]['subperiod_length']
        seconds_per_tick = parse_config(self.session.config['config_file'])[self.round_number-1]['seconds_per_tick']
        period_length = num_subperiods * ((subperiod_length + rest_length) * seconds_per_tick)
        return (
            num_subperiods *
            ((subperiod_length + rest_length) * seconds_per_tick)
        )

    def when_all_players_ready(self):
        super().when_all_players_ready()

        self.state = 'results'
        self.t = 0
        self.total_payoffs = {}
        self.countGood = {}
        self.periodResult = {}
        self.fixed_group_decisions = {}
        for i, player in enumerate(self.get_players()):
            self.total_payoffs[player.participant.code] = 0
            self.countGood[player.participant.code] = 0
            self.periodResult[player.participant.code] = ""
            self.fixed_group_decisions[player.participant.code] = 0
        self.save()

        emitter = DiscreteEventEmitter(
            parse_config(self.session.config['config_file'])[self.round_number-1]['seconds_per_tick'], self.period_length(), self, self.tick)
        emitter.start()

    def tick(self, current_interval, intervals):
        # TODO: Integrate into the otree-redwood DiscreteEventEmitter API, because otherwise
        # someone will forget this and get very confused when the tick functions use stale data.
        self.refresh_from_db()
        msg = {}
        
        if self.state == 'results':
            msg = {
                'realizedPayoffs': self.realized_payoffs(),
                # TODO: We don't really want to send this to the subjects, but we do want it saved
                # in the event - do we need server-private event fields?
                'fixedDecisions' : self.fixed_group_decisions
            }
            self.t += 1
            if self.t == parse_config(self.session.config['config_file'])[self.round_number-1]['subperiod_length']:
                msg['showAverage'] = True
                msg['showPayoffBars'] = True
                self.state = 'pause'
                self.t = 0
        elif self.state == 'pause':
            msg = {
                'payoffMatrix': parse_config(self.session.config['config_file'])[self.round_number-1]['payoff_matrix'],
                'probabilityMatrix': parse_config(self.session.config['config_file'])[self.round_number-1]['probability_matrix'],
                'numSubperiods': parse_config(self.session.config['config_file'])[self.round_number-1]['num_subperiods'],
                'pauseProgress': (self.t+1)/parse_config(self.session.config['config_file'])[self.round_number-1]['rest_length'],
                'fixedDecisions' : self.fixed_group_decisions,
                'countGood': self.countGood,
                'periodResult': self.periodResult,
                'totalPayoffs': self.total_payoffs,
                'subperiodLength': parse_config(self.session.config['config_file'])[self.round_number-1]['subperiod_length']
            }
            self.t += 1
            if self.t == parse_config(self.session.config['config_file'])[self.round_number-1]['rest_length']:
                msg['clearCurrentSubperiod'] = True
                self.state = 'results'
                self.t = 0
                for i, player in enumerate(self.get_players()):
                    self.total_payoffs[player.participant.code] = 0
                    self.countGood[player.participant.code] = 0
                    self.periodResult[player.participant.code] = ""
                    if player.participant.code in self.group_decisions:
                        self.fixed_group_decisions[player.participant.code] = self.group_decisions[player.participant.code]
        else:
            raise ValueError('invalid state {}'.format(self.state))

        self.send('tick', msg)
        self.save()


    def realized_payoffs(self):

        payoff_matrix = parse_config(self.session.config['config_file'])[self.round_number-1]['payoff_matrix']
        probability_matrix = parse_config(self.session.config['config_file'])[self.round_number-1]['probability_matrix']

        realized_payoffs = {}

        players = self.get_players()
        for i, player in enumerate(players):

            payoffs = [payoff_matrix[0][i], payoff_matrix[1][i], payoff_matrix[2][i], payoff_matrix[3][i]]
            probabilities = [probability_matrix[0][i], probability_matrix[1][i], probability_matrix[2][i], probability_matrix[3][i]]

            other = players[i-1]

            my_decision = self.fixed_group_decisions[player.participant.code]
            other_decision = self.fixed_group_decisions[other.participant.code]

            prob = ((my_decision * other_decision * probabilities[0]) +
                    (my_decision * (1 - other_decision) * probabilities[1]) +
                    ((1 - my_decision) * other_decision * probabilities[2]) +
                    ((1 - my_decision) * (1 - other_decision) * probabilities[3]))
            payoff_index = 0
            if random.random() <= prob:
                if my_decision:
                    payoff_index = 1
                    self.periodResult[player.participant.code] += "B"
                else:
                    payoff_index = 3
                    self.periodResult[player.participant.code] += "B"
            else:
                if my_decision:
                    payoff_index = 0
                    self.countGood[player.participant.code] += 1
                    self.periodResult[player.participant.code] += "G"
                else:
                    payoff_index = 2
                    self.countGood[player.participant.code] += 1
                    self.periodResult[player.participant.code] += "G"

            realized_payoffs[player.participant.code] = payoffs[payoff_index]
            self.total_payoffs[player.participant.code] += realized_payoffs[player.participant.code]

        return realized_payoffs


class Player(BasePlayer):

    def initial_decision(self):
        return 0

    def other_player(self):
        return self.get_others_in_group()[0]

    def set_payoff(self):
        ticks = Event.objects.filter(
            channel='tick',
            content_type=ContentType.objects.get_for_model(self.group),
            group_pk=self.group.pk)
        
        self.payoff = 0
        total_subperiods = 0
        for tick in ticks:
            if 'realizedPayoffs' in tick.value:
                self.payoff += tick.value['realizedPayoffs'][self.participant.code]
                total_subperiods += 1
        if total_subperiods:
            self.payoff /= total_subperiods
