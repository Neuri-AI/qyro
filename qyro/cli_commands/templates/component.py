QT_COMPONENT_TEMPLATE = f"""
from qyro_engine.core.base import Component, bootstrap
from qyro_engine.store import Pydux
from $Binding.QtWidgets import $Widget

@bootstrap
class $Name($Widget, Component, Pydux):

	def component_will_mount(self):
		self.subscribe_to_store(self)

	def render_(self):
		# Render the UI here
		pass
"""