# app/prediction/strength.py
# Turns stored data into the two numbers the maths in poisson.py needs: how many
# goals we expect each side to score (lambda). The only file in this package that
# touches the database - its source of truth is the standings table (goals scored
# and conceded per season), not live API calls.
#
# Strength is always measured RELATIVE to one league's average: an attack of 1.2
# means "20% better than a typical team in THIS league". That is why the predictor
# is within-league only - comparing two teams from different leagues would compare
# numbers built on two different baselines, which says nothing.

from sqlalchemy.orm import Session

from app import models
from app.constants import HOME_ADVANTAGE


class LeagueStrength:
    """Attack and defence strength of every team in one league and season.

    The whole table is read once, in the constructor, so predicting a full round
    of matches costs a single query instead of one per team. An instance is tied
    to one (league, season) pair and to the session it was built with, which is
    why models create one and never cache it between requests.
    """

    def __init__(self, db: Session, league_id: int, season: int):
        rows = (
            db.query(models.Standing)
            .filter(
                models.Standing.league_id == league_id,
                models.Standing.season == season,
            )
            .all()
        )

        # Two passes over the same rows on purpose: every strength is divided by
        # the league average, so the average has to be finished before the first
        # one can be computed. Walking twenty rows twice is still far cheaper
        # than asking the database a second time.
        sum_goals_for = 0
        sum_played = 0
        for row in rows:
            sum_goals_for += row.goals_for
            sum_played += row.played

        # Catches both "this league and season are not in the database" and "the
        # season has not kicked off yet" - with no matches played there is no
        # average to measure anybody against. Failing here tells the caller it
        # picked the wrong season; the alternative is every lambda silently
        # coming out as zero and a simulation in which nobody ever scores.
        if sum_played == 0:
            raise ValueError(
                f"No played matches for league {league_id} season {season} - "
                "cannot measure team strength."
            )

        # Goals scored by an average team in a single match. The denominator
        # counts every match twice, once in each side's row, and that is exactly
        # what makes this a per-team number instead of a per-match one - a lambda
        # describes one side of one match.
        self.base = sum_goals_for / sum_played

        self.strengths = {}
        for row in rows:
            # A team that has played nothing has no measurable strength, and
            # dividing by its played count would raise. Leaving it out of the
            # dict hands it the neutral default in attack_defence().
            if row.played != 0:
                attack = (row.goals_for / row.played) / self.base
                defence = (row.goals_against / row.played) / self.base
                self.strengths[row.team_id] = (attack, defence)

    def attack_defence(self, team_id: int) -> tuple[float, float]:
        """Strength of one team, or a neutral 1.0/1.0 when it is unknown.

        attack  > 1  -> scores more than an average team;  < 1 -> fewer.
        defence < 1  -> concedes fewer than average (good); > 1 -> worse.

        A promoted team has no row in this league's previous season, so there is
        nothing to measure it by and "exactly average" is the only honest guess.
        It flatters them - promoted sides are usually weaker than the average -
        but their real record sits in a division this project does not import.
        Doing better needs strengths that are comparable across leagues, which
        is a model of its own rather than a fix here.
        """
        if team_id not in self.strengths:
            return (1.0, 1.0)
        return self.strengths[team_id]

    def lambdas(self, home_id: int, away_id: int) -> tuple[float, float]:
        """Expected goals (lambda) for the home and away team in a league match."""
        home_attack, home_defence = self.attack_defence(home_id)
        away_attack, away_defence = self.attack_defence(away_id)
        # Expected goals = the league's average, scaled twice: by how good this
        # attack is and by how leaky the opponent's defence is. A strong attack
        # facing a weak defence multiplies up; two solid defences pull the number
        # down. HOME_ADVANTAGE multiplies the home side only - standings do not
        # split home from away goals, so a flat boost is the best this data
        # source allows.
        lam_home = self.base * home_attack * away_defence * HOME_ADVANTAGE
        lam_away = self.base * away_attack * home_defence
        return (lam_home, lam_away)
