"""Erros tipados da aplicação. A borda HTTP os converte em Problem Details (RFC 9457)."""


class AppError(Exception):
    status = 500
    slug = "internal-error"
    title = "Erro interno"

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status = 404
    slug = "not-found"
    title = "Recurso não encontrado"


class InvalidInputError(AppError):
    status = 422
    slug = "invalid-input"
    title = "Parâmetro inválido"


class UpstreamUnavailableError(AppError):
    status = 502
    slug = "upstream-unavailable"
    title = "Portal do TSE indisponível"


class UpstreamDataError(AppError):
    status = 502
    slug = "upstream-invalid-data"
    title = "Dado inválido recebido do TSE"


class ServiceUnavailableError(AppError):
    status = 503
    slug = "service-unavailable"
    title = "Serviço temporariamente indisponível"
