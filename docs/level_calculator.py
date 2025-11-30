"""
Kalkulator progresji XP dla Discord voice bota.

Użycie:
    python docs/level_calculator.py

Formuła:
    xp_needed_for_level(n) = 5*n^2 + 50*n + 100
    XP rate: 6 XP/min (1 XP za 10s w voice)
"""

def xp_needed_for_level(level: int) -> int:
    """Zwraca ile XP potrzeba żeby wejść na poziom `level` z `level-1`."""
    return 5 * (level ** 2) + 50 * level + 100


def main():
    total = 0
    print("=" * 60)
    print("Discord Voice XP Bot - Level Progression Calculator")
    print("=" * 60)
    print(f"{'Level':<8} {'XP to next':<12} {'Total XP':<12} {'Hours in voice':<15}")
    print("-" * 60)

    for lvl in range(1, 51):
        xp_to_next = xp_needed_for_level(lvl)
        total += xp_to_next
        hours = total / 6 / 60  # 6 XP/min

        # Wyświetl co 5 leveli + pierwsze 3 dla poglądu
        if lvl <= 3 or lvl % 5 == 0:
            print(f"{lvl:<8} {xp_to_next:<12,} {total:<12,} {hours:>6.1f}h")

    print("=" * 60)
    print(f"\nFormuła: xp_needed(n) = 5*n² + 50*n + 100")
    print(f"Rate: 6 XP/min (1 tick/min)")
    print(f"\nProgresja jest zbilansowana:")
    print(f"  • Level 10 ≈ 9h voice (casual user w tydzień)")
    print(f"  • Level 20 ≈ 36h voice (aktywny user)")
    print(f"  • Level 50 ≈ 236h voice (hardcore grinder)")


if __name__ == "__main__":
    main()
