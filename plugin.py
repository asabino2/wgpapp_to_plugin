import gradio as gr
from pathlib import Path

from shared.utils.plugins import WAN2GPPlugin

try:
    from .converter import generate_plugin
except ImportError:  # pragma: no cover
    generate_plugin = None


class WgpappToPluginPlugin(WAN2GPPlugin):
    def setup_ui(self):
        self.request_global("app")
        self.add_tab(
            tab_id="wgpapp_to_plugin",
            label="WGPApp → Plugin",
            component_constructor=self.create_config_ui,
        )

    def create_config_ui(self):
        with gr.Column() as layout:
            gr.Markdown("### WGPApp → Plugin\nConvert a .wgpapp bundle into a WanGP plugin.")
            package = gr.File(
                label=".wgpapp file",
                file_types=[".wgpapp"],
                type="filepath",
            )
            app_title = gr.Textbox(
                label="App title",
                placeholder="Type the app title or keep the default",
            )
            app_description = gr.Textbox(
                label="App description",
                placeholder="Optional description for the generated WanGP plugin",
            )
            output_dir = gr.Textbox(
                label="Output folder",
                placeholder="C:/wan2gp/plugins/my-app",
            )
            button = gr.Button("Generate plugin")
            result = gr.Markdown("")

        package.change(fn=self._read_app_metadata, inputs=[package], outputs=[app_title, app_description])
        button.click(fn=self._convert, inputs=[package, app_title, app_description, output_dir], outputs=[result])
        return layout

    def _read_app_metadata(self, package_file):
        if not package_file:
            return "", ""

        package_path = package_file
        if isinstance(package_path, (list, tuple)):
            package_path = package_path[0]
        if isinstance(package_path, dict):
            package_path = package_path.get("name") or package_path.get("path")

        try:
            from .converter import package_manifest

            manifest = package_manifest(Path(str(package_path)))
        except Exception:
            return "", ""

        return str(manifest.get("name") or "").strip(), str(manifest.get("description") or "").strip()

    def _convert(self, package_file, app_title, app_description, output_dir):
        if not package_file:
            return "Select a `.wgpapp` file before continuing."
        if not output_dir or not str(output_dir).strip():
            return "Please provide a valid output folder."
        if generate_plugin is None:
            return "The conversion function is not available in the current environment."

        package_path = package_file
        if isinstance(package_path, (list, tuple)):
            package_path = package_path[0]
        if isinstance(package_path, dict):
            package_path = package_path.get("name") or package_path.get("path")

        output_path = Path(str(output_dir)).expanduser()
        try:
            generated = generate_plugin(
                str(package_path),
                str(output_path),
                app_title=str(app_title).strip() if app_title else None,
                app_description=str(app_description).strip() if app_description else None,
            )
            return (
                "## Plugin generated successfully\n\n"
                f"- Source file: `{package_path}`\n"
                f"- Generated folder: `{generated}`\n\n"
                "Install it by copying this folder into the WanGP `plugins` subfolder or by using the GitHub URL in the plugin manager."
            )
        except Exception as exc:  # pragma: no cover - UI error reporting
            return f"### Error generating plugin\n\n```text\n{exc}\n```"
