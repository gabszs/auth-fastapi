from fastapi import APIRouter
from fastapi import status

from app.core.exceptions import http_errors

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get(
    "/bad-request",
    status_code=status.HTTP_400_BAD_REQUEST,
    summary="Exemplo de Bad Request",
    description="Retorna um erro 400 quando dados inválidos são enviados",
)
def trigger_bad_request():
    """
    Rota que demonstra o tratamento de erro 400 (Bad Request).
    Usado quando o cliente envia dados inválidos ou malformados.
    """
    raise http_errors.bad_request(
        detail="Os dados enviados são inválidos. Verifique o formato da requisição."
    )


@router.get(
    "/invalid-credentials",
    status_code=status.HTTP_401_UNAUTHORIZED,
    summary="Exemplo de Credenciais Inválidas",
    description="Retorna um erro 401 quando as credenciais de login são inválidas",
)
def trigger_invalid_credentials():
    """
    Rota que demonstra o tratamento de erro 401 (Unauthorized).
    Usado quando o usuário tenta fazer login com credenciais inválidas.
    """
    raise http_errors.invalid_credentials(
        detail="Email ou senha incorretos. Verifique suas credenciais."
    )


@router.get(
    "/auth-error",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Exemplo de Erro de Autenticação",
    description="Retorna um erro 403 quando o usuário não tem permissão",
)
def trigger_auth_error():
    """
    Rota que demonstra o tratamento de erro 403 (Forbidden).
    Usado quando o usuário autenticado não tem permissão para acessar o recurso.
    """
    raise http_errors.auth_error(
        detail="Você não tem permissão para acessar este recurso."
    )


@router.get(
    "/not-found",
    status_code=status.HTTP_404_NOT_FOUND,
    summary="Exemplo de Recurso Não Encontrado",
    description="Retorna um erro 404 quando o recurso não existe",
)
def trigger_not_found():
    """
    Rota que demonstra o tratamento de erro 404 (Not Found).
    Usado quando o recurso solicitado não existe.
    """
    raise http_errors.not_found(
        detail="O recurso solicitado não foi encontrado."
    )


@router.get(
    "/validation-error",
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    summary="Exemplo de Erro de Validação",
    description="Retorna um erro 422 quando há erro de validação",
)
def trigger_validation_error():
    """
    Rota que demonstra o tratamento de erro 422 (Unprocessable Entity).
    Usado quando os dados não passam na validação.
    """
    raise http_errors.validation_error(
        detail="Erro de validação: O campo 'email' deve ser um email válido."
    )


@router.get(
    "/duplicated-error",
    status_code=status.HTTP_409_CONFLICT,
    summary="Exemplo de Recurso Duplicado",
    description="Retorna um erro 409 quando há conflito de dados",
)
def trigger_duplicated_error():
    """
    Rota que demonstra o tratamento de erro 409 (Conflict).
    Usado quando há tentativa de criar um recurso que já existe.
    """
    raise http_errors.duplicated_error(
        detail="Este email já está registrado no sistema."
    )
