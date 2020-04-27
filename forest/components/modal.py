import bokeh.models
import bokeh.layouts
import forest.colors
from forest.observe import Observable
from forest import layers


class Modal:
    """Modal component"""
    def __init__(self, view=None):
        if view is None:
            view = Default()
        self.view = view
        self.layout = bokeh.layouts.column(
            self.view.layout,
            name="modal",
            sizing_mode="stretch_width")

    def connect(self, store):
        return self.view.connect(store)


class Default(Observable):
    """Standard interface for modal dialogue"""
    def __init__(self):
        self.views = {}
        self.views["layer"] = Layer()
        self.views["save"] = SaveEdit([self.views["layer"]])
        self.layout = bokeh.layouts.column(
            self.views["layer"].layout,
            self.views["save"].layout
        )

    def connect(self, store):
        self.views["layer"].connect(store)
        self.views["save"].connect(store)
        return self


class Tabbed:
    """Tabbed user interface"""
    def __init__(self):
        self.views = {}
        self.views["layer"] = Layer()
        self.views["settings"] = Settings()
        self.views["save"] = SaveEdit([
            self.views["layer"],
            self.views["settings"]
        ])
        self.layout = bokeh.layouts.column(
            bokeh.models.Tabs(tabs=[
                bokeh.models.Panel(
                    child=self.views["layer"].layout,
                    title="Layer"
                ),
                bokeh.models.Panel(
                    child=self.views["settings"].layout,
                    title="Settings"
                )]),
            self.views["save"].layout
        )

    def connect(self, store):
        self.views["layer"].connect(store)
        self.views["settings"].connect(store)
        self.views["save"].connect(store)
        return self


class SaveEdit(Observable):
    """Communicates save/edit state to Store"""
    def __init__(self, views):
        self.views = views
        buttons = (
            bokeh.models.Button(label="Save"),
            bokeh.models.Button(label="Exit"))
        buttons[0].on_click(self.on_save)
        for button in buttons:
            custom_js = bokeh.models.CustomJS(code="""
                let el = document.getElementById("modal");
                el.style.visibility = "hidden";
            """)
            button.js_on_click(custom_js)
        self.layout = bokeh.layouts.row(*buttons, sizing_mode="stretch_width")
        super().__init__()

    def connect(self, store):
        self.add_subscriber(store.dispatch)
        return self

    def on_save(self):
        # Send settings to forest.layers to process
        settings = {}
        for view in self.views:
            settings.update(view.settings())
        self.notify(layers.on_save(settings))


class Settings:
    """MapView settings"""
    def __init__(self):
        self.views = {}
        self.views["color_palette"] = forest.colors.ColorPalette()
        self.views["user_limits"] = forest.colors.UserLimits()
        self.layout = bokeh.layouts.column(
            self.views["color_palette"].layout,
            self.views["user_limits"].layout
        )

    def render(self, state):
        # Populate initial settings with current state
        # TODO: Get this state from stat["layers"] etc.
        fake_state = {
            "name": "Accent",
            "names": state.get("names", []),
            "number": 3,
            "numbers": state.get("numbers", []),
            "reverse": True,
            "invisible_min": True,
            "invisible_max": True,
            "limits": {
                "origin": "user",
                "user": {
                    "low": 0,
                    "high": 42
                },
                "column_data_source": {
                    "low": 0.1,
                    "high": 100.1,
                }
            }
        }
        self.views["color_palette"].render(fake_state)
        self.views["user_limits"].render(fake_state)

    def settings(self):
        # TODO: Replace with actual UI values, need to extend LayerSpec to
        #       support ColorSpec or an equivalent pointer to ColorSpec
        props = {}
        for view in self.views.values():
            props.update(view.props())
        return {
            "color_spec": forest.colors.parse_color_spec(props)
        }

    def connect(self, store):
        store.add_subscriber(self.render)
        return self


class Layer(Observable):
    """Standard modal dialogue user interface"""
    def __init__(self):
        self.div = bokeh.models.Div(text="Add layer",
                               css_classes=["custom"],
                               sizing_mode="stretch_width")
        self.inputs = {}

        # Text-input to name layer
        self.inputs["name"] = bokeh.models.TextInput(
            title="Name:",
            placeholder="Enter text")

        # Select layer settings, e.g. dataset, variable, etc.
        self.selects = {}
        self.selects["dataset"] = bokeh.models.Select(
            title="Dataset:",
            options=[])
        self.selects["variable"] = bokeh.models.Select(
            title="Variable:",
            options=[])
        self.source = bokeh.models.ColumnDataSource({
            "datasets":  [],
            "variables": []
        })

        # Variable options on source change
        custom_js = bokeh.models.CustomJS(
            args=dict(
                dataset_select=self.selects["dataset"],
                variable_select=self.selects["variable"]),
            code="""
                let source = cb_obj;
                forest.link_selects(dataset_select, variable_select, source);
        """)
        self.source.js_on_change("data", custom_js)

        # Variable options on dataset select change
        custom_js = bokeh.models.CustomJS(
            args=dict(
                variable_select=self.selects["variable"],
                source=self.source),
            code="""
                let dataset_select = cb_obj;
                forest.link_selects(dataset_select, variable_select, source);
        """)
        self.selects["dataset"].js_on_change("value", custom_js)
        self.layout = bokeh.layouts.column(
            self.div,
            self.inputs["name"],
            self.selects["dataset"],
            self.selects["variable"],
            sizing_mode="stretch_width")
        super().__init__()

    def connect(self, store):
        store.add_subscriber(self.render)
        self.add_subscriber(store.dispatch)
        return self

    def render(self, state):
        # Configure title
        mode = state.get("layers", {}).get("mode", {}).get("state", "add")
        self.div.text = {"edit": "Edit layer"}.get(mode, "Add layer")

        # Set name for layer, e.g. layer-0
        node = state
        for key in ("layers", "mode"):
            node = node.get(key, {})
        mode = node.get("state", "add")
        if mode == "edit":
            # Edit mode
            index = node["index"]
            settings = state["layers"]["index"][index]
            self.inputs["name"].value = settings["label"]
            if "dataset" in settings:
                self.selects["dataset"].value = settings["dataset"]
            if "variable" in settings:
                self.selects["variable"].value = settings["variable"]
        else:
            # Add mode
            self.inputs["name"].value = "layer-0"

        # Parse list of datasets from state
        datasets = self.to_props(state)

        # Configure dimension(s) source
        variables = []
        for label in datasets:
            texts = (state.get("dimension", {})
                          .get(label, {})
                          .get("variables", []))
            variables.append(texts)
        self.source.data = {
            "datasets": datasets,
            "variables": variables
        }

        # Configure available datasets
        self.selects["dataset"].options = datasets
        if len(self.selects["dataset"].options) > 0:
            if self.selects["dataset"].value == "":
                self.selects["dataset"].value = self.selects["dataset"].options[0]

    def to_props(self, state):
        return [name for name, _ in state.get("patterns", [])]

    def settings(self):
        # Send settings to forest.layers to process
        return {
            "label": self.inputs["name"].value,
            "dataset": self.selects["dataset"].value,
            "variable": self.selects["variable"].value
        }
