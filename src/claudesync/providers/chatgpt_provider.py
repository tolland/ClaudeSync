import openai
import os
from datetime import datetime, timezone
from .base_provider import BaseProvider
from ..exceptions import ProviderError


class ChatGPTProvider(BaseProvider):
    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.api_key = os.getenv("OPENAI_API_KEY") or (config and config.get("openai_api_key"))
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY not found in environment or config")
        openai.api_key = self.api_key

    def login(self):
        return self.api_key, datetime.now(timezone.utc).replace(year=2100)  # Fake expiry

    def get_organizations(self):
        return [{"id": "default", "name": "OpenAI"}]

    def get_projects(self, organization_id, include_archived=False):
        # Placeholder: OpenAI projects API is not fully public
        return [{"id": "default", "name": "ChatGPT Default Project", "archived_at": None}]

    def list_files(self, organization_id, project_id):
        try:
            files = openai.files.list()
            return [
                {
                    "uuid": f.id,
                    "file_name": f.filename,
                    "created_at": f.created_at,
                    "content": None,
                }
                for f in files.data
            ]
        except Exception as e:
            raise ProviderError(str(e))

    def upload_file(self, organization_id, project_id, file_name, content):
        try:
            from io import BytesIO
            file_obj = BytesIO(content.encode("utf-8"))
            result = openai.files.create(file=file_obj, purpose="assistants", file_name=file_name)
            return result
        except Exception as e:
            raise ProviderError(str(e))

    def delete_file(self, organization_id, project_id, file_uuid):
        try:
            openai.files.delete(file_uuid)
        except Exception as e:
            raise ProviderError(str(e))

    def archive_project(self, organization_id, project_id):
        return None  # Not supported

    def create_project(self, organization_id, name, description=""):
        return {"id": "default", "name": name}  # Placeholder

    def get_chat_conversations(self, organization_id):
        return []  # Threads are not listed via public API yet

    def get_chat_conversation(self, organization_id, conversation_id):
        return openai.beta.threads.messages.list(thread_id=conversation_id)

    def delete_chat(self, organization_id, conversation_uuids):
        return None  # Not supported

    def create_chat(self, organization_id, chat_name="", project_uuid=None, model=None):
        try:
            thread = openai.beta.threads.create()
            return {"id": thread.id, "name": chat_name}
        except Exception as e:
            raise ProviderError(str(e))

    def send_message(self, organization_id, chat_id, prompt, timezone="UTC", model=None):
        try:
            openai.beta.threads.messages.create(
                thread_id=chat_id,
                role="user",
                content=prompt,
            )
            run = openai.beta.threads.runs.create(
                thread_id=chat_id,
                assistant_id=self.config.get("assistant_id"),
            )
            while True:
                run = openai.beta.threads.runs.retrieve(thread_id=chat_id, run_id=run.id)
                if run.status == "completed":
                    messages = openai.beta.threads.messages.list(thread_id=chat_id)
                    return messages.data
                elif run.status in ("failed", "cancelled"):
                    raise ProviderError(f"Run failed: {run.status}")
        except Exception as e:
            raise ProviderError(str(e))

    def get_published_artifacts(self, organization_id):
        return []

    def get_artifact_content(self, organization_id, artifact_uuid):
        return None
