export type AliasWordList = readonly string[]

export const defaultAdjectives: AliasWordList = [
    "curious",
    "thoughtful",
    "clever",
    "patient",
    "bold",
    "careful",
    "precise",
    "methodical",
    "gentle",
    "swift",
]

export const defaultAnimals: AliasWordList = [
    "duck",
    "otter",
    "fox",
    "owl",
    "panda",
    "sparrow",
    "lynx",
    "beaver",
    "hedgehog",
    "heron",
]

export function generateAlias(
    adjectives: AliasWordList = defaultAdjectives,
    animals: AliasWordList = defaultAnimals,
    separator = "-",
): string {
    if (!adjectives.length || !animals.length) {
        return "anonymous-reviewer"
    }

    const adj = adjectives[Math.floor(Math.random() * adjectives.length)]
    const animal = animals[Math.floor(Math.random() * animals.length)]

    return `${adj}${separator}${animal}`
}
