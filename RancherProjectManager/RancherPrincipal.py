from typing import Dict

class RancherPrincipal:
    def __init__(self, json_data: Dict):
        try:
            self.id = json_data['id']
            self.type = json_data['principalType']
            self.is_group = self.type == 'group'
            self.name = json_data['name']
        except KeyError as e:
            raise ValueError from e

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
      return isinstance(other, self.__class__) and other and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "RancherPrincipal(" + self.id + ")"

    def __str__(self):
        return self.type + " " + self.name + " (" + self.id + ")"
 
