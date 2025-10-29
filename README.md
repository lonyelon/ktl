# KTL (**K**e**T**tlebel**L**)

KTL is a command-line tool for plaintext fitness, weight and nutrition tracking.
It supports both strength and cardio exercises.

## Example YAML journal

```yaml
# (MANDATORY) defines the config for the database.
config:
  # (OPTIONAL) tags we want to have for our exercises
  tags: [legs, quads, main]

  # (OPTIONAL) exercises we are going to have in our journal.
  exercises:
    run:
      # (MANDATORY) can be distance-cardio or strength. In this case, this is
      # clearly cardio.
      type: distance-cardio
      
      # (OPTIONAL) some tags for filtering if we want. They have to be defined
      # in config.tags.
      tags: [main]

    # More exercises.
    squat:
      type: strength
      tags: [main, legs, quads]
    front-squat:
      type: strength
      tags: [main, legs, quads]

# (MANDATORY) journal data.
journal:

  # Each key is a date.
  2025-10-19:
    # (OPTIONAL) we can register our weight in both kg and lbs:
    meassurements:
      weight: 90kg

    # (OPTIONAL) workout for the day. In this case two exercises from the
    # config.exercises list were performed.
    # Important! the notation for sets is very particular, and all of the
    # following can be combined in one string:
    #   TEMPLATE                                  EXAMPLE         EXAMPLE EXPLANATION
    #   <weight><unit>x<reps>x<sets>              100kgx10x3      3 sets of 10 reps with 100 kilograms.
    #   <weight><unit>x<reps>                     80lbsx7         One set of 7 reps with 80 pounds.
    #                                                             Equivalent to: 80lbsx7x1.
    #   <weight><unit>x(<reps_0>+<reps_1>+...)    10kgx(5+3+1)    Three sets with 10 kilograms, each with different reps.
    #                                                             Equivalent to: 10kgx5 10kgx3 10kgx1.
    #   <reps>x<sets>                             8x5             5 sets of 8 reps without extra weight (maybe pull-ups?).
    #                                                             Equivalent to: 0kgx8x52
    #   <reps>                                    20              One set of 20 reps without extra weight.
    #                                                             Equivalent to: 20x1.
    workout:
      squat: 100kgx5x5
      front-squat: 80kgx8x3 70kgx(8+7+5)
```

## Usage

Right now, the only way to interface with KTL is throw `KTL-query`, a tool that converts the YAML journal into a in-memory `sqlite3` database.
It can be used from the command line or as a python module.

For example, to get your PRs for each rep count in the front squat you can make the following query:

```sh
ktl-query '
  SELECT reps, MAX(weight)
  FROM strength_sets
  WHERE exercise = "front-squat"
  GROUP BY reps
' FILE.yaml
```

Or to list your weight for each day:
```sh
ktl-query '
  SELECT date, weight
  FROM meassurements
' FILE.yaml
```

## Installation

Right now, the easiest way to use KTl is through the nix flake:
```sh
nix run github:lonyelon/ktl#ktl-query QUERY FILE
```
