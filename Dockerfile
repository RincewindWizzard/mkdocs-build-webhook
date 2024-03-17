FROM python:3.12 AS builder
RUN pip install poetry
WORKDIR /app
COPY README.md pyproject.toml poetry.lock ./
COPY mkdocs_build_webhook /app/mkdocs_build_webhook/
RUN poetry install --no-root --no-interaction --no-ansi
RUN find
RUN poetry build


FROM python:3.12-slim
ENV WEBHOOK_GIT_DIR=/git/
ENV WEBHOOK_WWW_DIR=/var/www/
ENV WEBHOOK_SECRET="<your webhook secret>"


WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git

#RUN pip install gunicorn

COPY --from=builder /app/dist/mkdocs_build_webhook*.whl /app/dist/
COPY entrypoint.sh /app/
COPY docker/ssh_config /home/user/.ssh/config

RUN pip install dist/mkdocs_build_webhook-*.whl
RUN rm -r /app/dist/



RUN adduser --disabled-password --gecos '' --uid 1000 user

RUN mkdir -p /git/ /var/www/
RUN chown -R user /home/user/ /var/www/ /git/

USER user



RUN ssh-keyscan github.com >> /home/user/.ssh/known_hosts




#COPY --from=builder /app .




EXPOSE 5000
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "mkdocs_build_webhook.__main__:app"]
CMD ["/bin/bash", "entrypoint.sh"]