from dataclasses import dataclass

from backend.application.users.user_accounts import UserProfileRecord


@dataclass(frozen=True)
class GetCurrentUserProfileCommand:
    user_profile: UserProfileRecord


class GetCurrentUserProfile:
    def execute(self, *, command: GetCurrentUserProfileCommand) -> UserProfileRecord:
        return command.user_profile
