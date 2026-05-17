"""Test data factories for evolution-engine types.

Builder pattern with fluent API for constructing test objects.
Every factory produces valid objects by default; override via chainable methods.

Usage:
    genome = RealGenomeFactory.build()
    individual = IndividualFactory.build(genome=genome)
    population = PopulationFactory.build(size=20)
    stats = GenerationStatsFactory.build()
"""
