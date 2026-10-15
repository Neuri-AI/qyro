"""Qyro Component page widgets composed into the main tab layout."""

from views.root import Root
from components import UserCard

class ComponentsView(Root):
    def component_did_mount(self):
        self.layout.addWidget(UserCard(
            parent=self, name="Ada Lovelace", role="Arquitecta de software"
        ))
        self.layout.addWidget(UserCard(
            parent=self, props={"name": "Linus Torvalds"}, role="Mantenedor"
        ))