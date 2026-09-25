import os

from hypothesis import settings

# HYPOTHESIS_PROFILE=fuzz runs a long fuzzing session instead of the quick default.
settings.register_profile('fuzz', max_examples=10_000, deadline=None)
settings.load_profile(os.environ.get('HYPOTHESIS_PROFILE', 'default'))
