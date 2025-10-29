#!/usr/bin/env python3

import argparse
import datetime
import re
import sqlite3
import sys
import yaml


class _ExerciseSet:
    value: float = 0.0
    unit: str    = 'kg'
    reps: int    = 1

    def __init__(self, value: float, unit: str, reps: float):
        self.value = value
        self.unit = unit
        self.reps = reps

    def __repr__(self):
        return f"{self.value}{self.unit}x{self.reps}"

    def __str__(self):
        return self.__repr__()


class _DistanceCardioSet:
    distance: float = 0.0
    distance_unit: str = 'm'
    speed: float = 0.0
    speed_unit: str = 'min/km'

    def __init__(self, distance: float, distance_unit: str):
        self.distance = distance
        self.distance_unit = distance_unit

    def __init__(self, distance: float, distance_unit: str, speed: float, speed_unit: str):
        self.distance = distance
        self.distance_unit = distance_unit
        self.speed = speed
        self.speed_unit = speed_unit

    def __repr__(self):
        if self.speed != 0.0:
            return f"{self.distance}{self.distance_unit} at {self.speed}{self.speed_unit} pace"
        return f"{self.distance}{self.distance_unit}"

    def __str__(self):
        return self.__repr__()


def _parse_strength_set(text: str) -> str:
    set_list = list()
    parts = text.split('x')
    if re.match(r'^[0-9]+(\.[0-9]+)?(kg|lbs)(x[0-9]+(x[0-9]+)?)?$', text):
        weight = float(re.sub(r'[A-Za-z]+$', '', parts[0]))
        unit = re.sub(r'^[0-9]+(\.[0-9]+)?', '', parts[0])
        reps = 1 if len(parts) == 1 else int(parts[1])
        set_count = 1 if len(parts) != 3 else int(parts[2])
        for i in range(set_count):
            set_list += [_ExerciseSet(weight, unit, reps)]
    elif re.match(r'^[0-9]+(\.[0-9]+)?(kg|lbs)x\([0-9]+(\+[0-9]+)*\)$', text):
        weight = float(re.sub(r'[A-Za-z]+$', '', parts[0]))
        unit = re.sub(r'^[0-9]+(\.[0-9]+)?', '', parts[0])
        for s in parts[1][1:-1].split('+'):
            reps = int(s)
            set_list += [_ExerciseSet(weight, unit, reps)]
    elif re.match(r'^[0-9]+(x[0-9]+)?$', text):
        weight = 0
        unit = 'kg'
        reps = int(parts[0])
        set_count = 1 if len(parts) != 2 else int(parts[1])
        for i in range(set_count):
            set_list += [_ExerciseSet(weight, unit, reps)]
    return set_list


def _parse_strength_exercise(input_set_list) -> str:
    """Define here what to do with the input string."""

    sets = list()
    if isinstance(input_set_list, str):
        input_set_list = [input_set_list]
    for text in input_set_list:
        text = text.replace(' ', '+')
        text = text.replace('\n', '')

        set_start = 0
        parenthesis = 0
        for i, v in enumerate(text):
            if v == '(':
                parenthesis += 1
            elif v == ')':
                parenthesis -= 1
                if parenthesis == 0:
                    sets += _parse_strength_set(text[set_start:i + 1])
            elif v == '+' and parenthesis == 0:
                sets += _parse_strength_set(text[set_start:i])
                set_start = i + 1
            elif i == len(text) - 1:
                sets += _parse_strength_set(text[set_start:i + 1])
    return sets


def _parse_endurance_exercise(input_set_list) -> str:
    """Define here what to do with the input string."""

    sets = list()
    if isinstance(input_set_list, str):
        input_set_list = [input_set_list]
    for text in input_set_list:
        text = text.replace(' ', '+')
        text = text.replace('\n', '')
        for exercise_set in text.split('+'):
            parts = exercise_set.split('@')
            distance = float(re.sub(r'[a-z]$', '', parts[0]))
            unit = re.sub(r'^[0-9]+(\.[0-9]+)?', '', parts[0])
            if len(parts) == 2:
                speed = float(re.sub(r'[a-z/]+$', '', parts[1]))
                speed_unit = re.sub(r'^[0-9](\.[0-9]+)?', '', parts[1])
                sets += [_DistanceCardioSet(distance, unit, speed, speed_unit)]
            else:
                sets += [_DistanceCardioSet(distance, unit)]
    return sets


def load(file):
    with open(file, 'r') as f:
        data = yaml.safe_load(f.read())

    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE tags(name)')
    cursor.execute('CREATE TABLE exercises(name, type)')
    cursor.execute('CREATE TABLE exercise_tags(exercise, tag)')
    cursor.execute('CREATE TABLE nutrition(date, calories)')
    cursor.execute('CREATE TABLE measurements(date, weight, weight_unit)')
    cursor.execute('CREATE TABLE strength_sets(date, exercise, weight, unit, reps)')
    cursor.execute('CREATE TABLE endurance_sets(date, exercise, distance, distance_unit, time, time_unit, speed, speed_unit)')

    if 'config' in data:
        if 'tags' in data['config']:
            for tag in data['config']['tags']:
                cursor.execute(f'INSERT INTO tags VALUES ("{tag}")')
        if 'exercises' in data['config']:
            for exercise_name, exercise_data in data['config']['exercises'].items():
                cursor.execute(f'INSERT INTO exercises VALUES ("{exercise_name}", "{exercise_data["type"]}")')
                if 'tags' in exercise_data:
                    for tag in exercise_data['tags']:
                        cursor.execute(f'INSERT INTO exercise_tags VALUES ("{exercise_name}", "{tag}")')
        else:
            raise KeyError('No exercises defined in config.exercises')
    else:
        raise KeyError('No config defined')

    if 'journal' in data:
        for date_name, date_data in sorted(data['journal'].items()):
            if 'workout' in date_data:
                for exercise_name, exercise_data in date_data['workout'].items():
                    if exercise_name in data['config']['exercises']:
                        if 'type' in data['config']['exercises'][exercise_name]:
                            if data['config']['exercises'][exercise_name]['type'] == 'strength':
                                for eset in _parse_strength_exercise(str(exercise_data)):
                                    cursor.execute(f'''
                                        INSERT INTO strength_sets
                                        VALUES ("{date_name}",
                                                "{exercise_name}",
                                                "{eset.value}",
                                                "{eset.unit}",
                                                "{eset.reps}")''')
                        else:
                            raise KeyError(f'Exercise "{exercise_name}" has no type set in config.exercises.{exercise_name}"')
                    else:
                        raise NameError(f'Exercise "{exercise_name}" for date "{date_name}" is not defined in config.exercises."')
            if 'nutrition' in date_data:
                if 'calories' in date_data['nutrition']:
                    if isinstance(date_data['nutrition']['calories'], dict):
                        if not 'min' in date_data['nutrition']['calories']:
                            raise NameError(f'journal.{date_name}.nutrition.calories is a dict but has no "min" key')
                        if not 'max' in date_data['nutrition']['calories']:
                            raise NameError(f'journal.{date_name}.nutrition.calories is a dict but has no "max" key')
                        calories = (date_data['nutrition']['calories']['min'] + date_data['nutrition']['calories']['max']) / 2
                        cursor.execute(f'INSERT INTO nutrition VALUES ("{date_name}", "{int(calories)}")')
                    else:
                        cursor.execute(f'INSERT INTO nutrition VALUES ("{date_name}", "{date_data["nutrition"]["calories"]}")')
            if 'measurements' in date_data:
                if 'weight' in date_data['measurements']:
                    weight = re.sub(r'[a-z]+$', '', date_data['measurements']['weight'])
                    unit = re.sub(r'^[0-9]+(\.[0-9]+)?', '', date_data['measurements']['weight'])

                    if unit != 'kg' and unit != 'lbs':
                        raise ValueError(f'journal.{date_name}.meassuremets.weight has an invalid unit: "{unit}"')

                    cursor.execute(f'''
                        INSERT INTO measurements
                        VALUES ("{date_name}",
                                "{weight}",
                                "{unit}")''')

    conn.commit()
    return conn


def _print_list(L):
    maxx = [0.0 for i in range(0, len(L[0]))]
    for l in L:
        for i, e in enumerate(l):
            if maxx[i] < len(e):
                maxx[i] = len(e)
    for l in L:
        for i, e in enumerate(l):
            print(e, end=' ' * (maxx[i] - len(e) + 1))
        print()


def main():
    connection = load(sys.argv[2])

    cursor = connection.cursor()
    cursor.execute(sys.argv[1])

    out_data = [[d[0] for d in cursor.description]] + cursor.fetchall()
    _print_list(out_data)

    connection.close()


if __name__ == "__main__":
    main()
