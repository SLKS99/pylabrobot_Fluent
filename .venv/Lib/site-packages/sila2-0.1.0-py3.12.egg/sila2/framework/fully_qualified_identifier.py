class FullyQualifiedIdentifier(str):
    def __eq__(self, other):
        if isinstance(other, str):
            return self.lower() == other.lower()

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __hash__(self):
        return super().lower().__hash__()
