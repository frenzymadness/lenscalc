from sympy import symbols, Eq
from sympy.core.symbol import Symbol
from sympy.core.expr import Expr
from sympy.solvers import solve


class Lens:
    variables = "D1", "D2", "D", "n1", "nL", "n2", "r1", "r2", "CT", "P1", "P2", "f1", "f2", "EFL", "FFL", "BFL", "NPS"

    for variable in variables:
        vars()[variable] = symbols(variable)

    equations = (
        Eq(D1, (nL - n1) / r1),
        Eq(D2, (n2 - nL) / r2),
        Eq(D, D1 + D2 - D1 * D2 * (CT / nL)),
        Eq(P1, (D2 / D) * (n1 / nL) * CT),
        Eq(P2, -(D1 / D) * (n2 / nL) * CT),
        Eq(EFL, 1 / D),
        Eq(f1, -n1 * EFL),
        Eq(f2, n2 * EFL),
        Eq(BFL, f2 + P2),
        Eq(FFL, f1 + P1),
        Eq(NPS, f2 + f1),
    )

    def __init__(self, *, D1=None, D2=None, D=None, n1=None, nL=None, n2=None, r1=None, r2=None, CT=None, P1=None, P2=None, f1=None, f2=None, EFL=None, FFL=None, BFL=None, NPS=None):
        self.parameters = locals()
        del self.parameters["self"]
    
    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)

        if isinstance(attr, Symbol):
            try:
                return self.parameters[name]
            except KeyError:
                raise AttributeError
        else:
            return attr

    def __setattr__(self, name, value):
        try:
            if name in self.parameters:
                self.parameters[name] = value
                return
        except AttributeError:
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)

    def _calculate_replacements(self):
        result = {}
        for variable in self.variables:
            if self.parameters[variable] is not None:
                result[variable] = self.parameters[variable]
        
        return result

    def calculate(self):
        self.replacements = self._calculate_replacements()
        missing_values = {symbols(v) for v in self.variables if v not in self.replacements}

        if not missing_values:
            print("Nothing to compute. All variables have their values!")
            return

        # Copy the lens equations to later manipulate with them.
        self.equations = list(self.equations)

        equation_index = 0
        while missing_values and equation_index < len(self.equations):
            equation = self.equations[equation_index]
            common = missing_values & equation.free_symbols

            if not common:
                self.equations.remove(equation)

            elif len(common) == 1:
                variable = list(common)[0]
                solved_equation = solve(equation, variable)

                if isinstance(solved_equation, list):
                    solved_equation = solved_equation[0]

                if isinstance(solved_equation, dict):
                    self.replacements[variable] = solved_equation[variable].subs(self.replacements)

                if isinstance(solved_equation, Expr):
                    self.replacements[variable] = solved_equation.subs(self.replacements)

                setattr(self, str(variable), self.replacements[variable])
                missing_values.remove(variable)
                self.equations.remove(equation)
                equation_index = 0

            else:
                equation_index += 1

        if not missing_values:
            return

        missing_values = [str(variable) for variable in missing_values]
        solved_equations = solve(self.equations, missing_values)
        if isinstance(solved_equations, dict):
            for variable in missing_values:
                setattr(self, variable, solved_equations[symbols(variable)].subs(self.replacements))
            return

        if not len(solved_equations):
            raise ValueError("SymPy doesn't want to calculate this input!")

        for variable, solved_equation in zip(missing_values, solved_equations[0]):
            setattr(self, variable, solved_equation.subs(self.replacements))

    def __str__(self):
        return "\n".join(f"{var}: {self.parameters[var]}" for var in self.variables)
    
    def __repr__(self):
        return self.__str__()
