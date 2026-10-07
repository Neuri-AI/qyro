"""Qyro Component page widgets composed into the main tab layout."""
from components import CounterCard, ProfileEditor, ProfilePreview, UserCard
from store import store
from views.root import Root


class PayloadsView(Root):
    def component_did_mount(self):
        self.profile_editor = ProfileEditor(
            parent=self, title="Componente emisor")
        self.profile_preview = ProfilePreview(
            parent=self, title="Componente receptor")
        self.layout.addWidget(self.profile_editor)
        self.layout.addWidget(self.profile_preview)

    def cleanup(self):
        self.profile_preview.component_will_unmount()
