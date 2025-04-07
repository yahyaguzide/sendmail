import os
import hvac
from hvac.exceptions import VaultDown, InvalidRequest, InvalidPath, VaultError


def get_vault_secret(
    secret_path: str,
    vault_url: str,
    mount_point: str = "kv",
) -> dict[str, str]:
    client_cert_path = os.environ.get("VAULT_CERT")
    client_key_path = os.environ.get("VAULT_KEY")

    try:
        # Initialize client
        client = hvac.Client(url=vault_url)

        client.auth.cert.login(cert_pem=client_cert_path, key_pem=client_key_path)

        # Verify authentication
        if not client.is_authenticated():
            raise VaultError("Authentication failed - invalid or missing token")

        response = client.secrets.kv.v2.read_secret_version(
            path=secret_path, mount_point=mount_point
        )
        secret_data = response.get("data", {}).get("data", {})

        if not secret_data:
            raise InvalidPath(f"No data found at path: {secret_path}")

        return secret_data

    except VaultDown as e:
        raise ConnectionError(f"Vault server unavailable: {e}") from e
    except InvalidPath as e:
        raise ValueError(f"Invalid secret path: {e}") from e
    except InvalidRequest as e:
        raise ValueError(f"Invalid request: {e}") from e
    except VaultError as e:
        raise RuntimeError(f"Vault operation failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}") from e
