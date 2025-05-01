"""Ce fichier contient une implémentation de la résolution de Sudoku en utilisant Gophersat."""

from copy import copy
from typing import List, Tuple
import subprocess
from itertools import combinations


# alias de types
Grid = List[List[int]]
PropositionnalVariable = int
Literal = int
Clause = List[Literal]
ClauseBase = List[Clause]
Model = List[Literal]

example: Grid = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


example2: Grid = [
    [0, 0, 0, 0, 2, 7, 5, 8, 0],
    [1, 0, 0, 0, 0, 0, 0, 4, 6],
    [0, 0, 0, 0, 0, 9, 0, 0, 0],
    [0, 0, 3, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 5, 0, 2, 0],
    [0, 0, 0, 8, 1, 0, 0, 0, 0],
    [4, 0, 6, 3, 0, 1, 0, 0, 9],
    [8, 0, 0, 0, 0, 0, 0, 0, 0],
    [7, 2, 0, 0, 0, 0, 3, 1, 0],
]


empty_grid: Grid = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]


#### fonctions fournies


def write_dimacs_file(dimacs: str, filename: str):
    """Écrit une chaîne DIMACS donnée en paramètre
    dans un fichier dont le nom donné en paramètre"""
    with open(filename, "w", newline="", encoding="utf-8") as cnf:
        cnf.write(dimacs)


def exec_gophersat(
    filename: str,
    cmd: str = "gophersat_executables/gophersat.exe",
    encoding: str = "utf8",
) -> Tuple[bool, List[int]]:
    """Exécute Gophersat sur le fichier donné en paramètre et retourne le résultat"""
    result = subprocess.run(
        [cmd, filename], capture_output=True, check=True, encoding=encoding
    )
    string = str(result.stdout)
    lines = string.splitlines()

    if lines[1] != "s SATISFIABLE":
        return False, []

    model = lines[2][2:-2].split(" ")

    return True, [int(x) for x in model]


####


def cell_to_variable(i: int, j: int, val: int) -> PropositionnalVariable:
    """Convertit une cellule (i, j) et une valeur val en une variable propositionnelle"""
    # La variable est numérotée de 1 à 729
    return 81 * i + 9 * j + val + 1


def variable_to_cell(var: PropositionnalVariable) -> tuple[int, int, int]:
    """Convertit une variable propositionnelle en une cellule (i, j) et une valeur val"""
    var -= 1
    val: int = var % 9
    var = var // 9
    j: int = var % 9
    var = var // 9
    i: int = var % 9
    return (i, j, val)


def model_to_grid(model: Model) -> Grid:
    """Convertit un modèle (une liste de variables) en une grille de Sudoku"""
    ### size(model) == 729
    sol: Grid = empty_grid
    i: int
    j: int
    val: int
    for var in model:
        if var > 0:
            [i, j, val] = variable_to_cell(var)
            sol[i][j] = val + 1
    return sol


def at_least_one(variables: List[PropositionnalVariable]) -> Clause:
    """Retourne une clause représentant la contrainte
    'au moins une des variables données est vraie'"""
    return copy(variables)


def at_most_ones(variables: List[PropositionnalVariable]) -> ClauseBase:
    """Retourne une base de clauses représentant
    la contrainte 'au plus une des variables données est vraie'"""
    cnf: List[List[PropositionnalVariable]] = []
    for comb in combinations(variables, 2):
        cnf += [[-1 * comb[0], -1 * comb[1]]]
    return cnf


def unique(variables: List[PropositionnalVariable]) -> ClauseBase:
    """Retourne une base de clauses représentant
    la contrainte 'exactement une des variables données est vraie'"""
    return [at_least_one(variables)] + at_most_ones(variables)


def create_cell_constraints() -> ClauseBase:
    """Retourne une base de clauses représentant
    la contrainte 'chaque cellule contient exactement une valeur'"""
    clause_base: ClauseBase = []
    for i in range(9):
        for j in range(9):
            clause_base += unique([cell_to_variable(i, j, val) for val in range(9)])
    return clause_base


def create_line_constraints() -> ClauseBase:
    """Retourne une base de clauses représentant la contrainte
    'chaque valeur (1 à 9) apparaît au moins une fois dans chaque ligne'"""
    return [
        at_least_one([cell_to_variable(i, j, val) for j in range(9)])
        for val in range(9)
        for i in range(9)
    ]


def create_column_constraints() -> ClauseBase:
    """Retourne une base de clauses représentant la contrainte
    'chaque valeur (1 à 9) apparaît au moins une fois dans chaque colonne'"""
    return [
        at_least_one([cell_to_variable(i, j, val) for i in range(9)])
        for val in range(9)
        for j in range(9)
    ]


def create_box_constraints() -> ClauseBase:
    """Retourne une base de clauses représentant la contrainte
    'chaque valeur (1 à 9) apparaît au moins une fois dans chaque boîte de 3x3'"""
    return [
        at_least_one(
            [
                cell_to_variable(i + box_line * 3, j + box_col * 3, val)
                for i in range(3)
                for j in range(3)
            ]
        )
        for box_line in range(3)
        for box_col in range(3)
        for val in range(9)
    ]


def create_value_constraints(grid: Grid) -> ClauseBase:
    """Etant donné une grille de Sudoku, retourne une base de clauses représentant
    les contraintes induites par les valeurs inscrites dans la grille"""
    return [
        [cell_to_variable(i, j, grid[i][j] - 1)]
        for i in range(9)
        for j in range(9)
        if grid[i][j] != 0
    ]


def generate_problem(grid: Grid) -> ClauseBase:
    """Génère la base de clauses représentant
    le problème de Sudoku rerpésenté par la grille donnée"""
    return (
        create_cell_constraints()
        + create_line_constraints()
        + create_column_constraints()
        + create_box_constraints()
        + create_value_constraints(grid)
    )


def clauses_to_dimacs(clauses: ClauseBase, nb_vars: int) -> str:
    """Convertit une base de clauses en une chaîne DIMACS"""
    dimacs: str = f"p cnf {nb_vars} {len(clauses)}\n"
    for clause in clauses:
        dimacs += " ".join([str(lit) for lit in clause]) + " 0\n"
    return dimacs


#### fonction principale
def resolve_sudoku(grid: Grid) -> Tuple[bool, Grid]:
    """Résout une grille de Sudoku en utilisant Gophersat"""
    clause_base = generate_problem(grid)
    dimacs = clauses_to_dimacs(clause_base, 729)
    write_dimacs_file(dimacs, "sudoku.cnf")
    result = exec_gophersat("sudoku.cnf")
    if result[0]:
        return True, model_to_grid(result[1])
    return False, []


def print_grid(grid: Grid) -> None:
    """Affiche une grille de Sudoku"""
    for i in range(9):
        if i % 3 == 0:
            print("-" * 25)
        print("| ", end="")
        for j in range(9):
            if grid[i][j] == 0:
                print(".", end=" ")
            else:
                print(grid[i][j], end=" ")
            if j % 3 == 2:
                print("| ", end="")
        print()
    print("-" * 25)


def verify_unique_solution(grid: Grid) -> bool:
    """Vérifie si la grille de Sudoku a une solution unique,
    sinon cela veut dire qu'elle n'est pas une grille de Sudoku valide"""
    clause_base = generate_problem(grid)
    dimacs = clauses_to_dimacs(clause_base, 729)
    write_dimacs_file(dimacs, "sudoku.cnf")
    result = exec_gophersat("sudoku.cnf")

    # Vérifier si la solution est unique si elle existe
    if result[0]:
        # Injecter la solution trouvée dans la base de clauses
        model = result[1]
        clause_base += [[-i for i in model]]
        dimacs = clauses_to_dimacs(clause_base, 729)
        write_dimacs_file(dimacs, "sudoku.cnf")
        result = exec_gophersat("sudoku.cnf")
        # Si la résolution est satisfaisable, cela signifie qu'il y a plus d'une solution
        return not result[0]
    # Si la résolution échoue, cela signifie qu'il n'y a pas de solution
    return False


def main():
    """Fonction principale pour exécuter le programme"""
    sudoku = example
    # Résoudre le Sudoku
    print("Sudoku à résoudre :")
    print_grid(sudoku)
    print("Résolution en cours...")
    result = resolve_sudoku(sudoku)
    if not result[0]:
        print("Aucune solution trouvée.")
    else:
        print("Solution trouvée :")
        print_grid(result[1])

    if verify_unique_solution(sudoku):
        print("La grille a une solution unique.")
    else:
        print("La grille n'a pas de solution unique.")


if __name__ == "__main__":
    main()
