#Confirmação da Operação (código 1) – confirmando a ocorrência da operação e o recebimento da mercadoria (para as operações com circulação de mercadoria);

#Desconhecimento da Operação (código 3) – declarando o desconhecimento da operação;

#Operação Não Realizada (código 4) – declarando que a operação não foi realizada (com recusa do Recebimento da mercadoria e outros) e a justificativa do porquê a operação não se realizou;

#Ciência da Emissão (ou Ciência da Operação) (código 2) – declarando ter ciência da operação destinada ao CNPJ, mas ainda não possuir elementos suficientes para apresentar uma manifestação conclusiva, como as acima citadas. Este evento era chamado de Ciência da Operação.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pynfe.processamento.comunicacao import ComunicacaoSefaz
from pynfe.processamento.serializacao import SerializacaoXML
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.entidades.evento import EventoManifestacaoDest
from pynfe.entidades.fonte_dados import _fonte_dados
import datetime

app = FastAPI(title="Manifestação Destinatário", version="1.0", description="Através dos dados informados esse sistema busca todas as notas emitidas contra um CNPJ.")

# Modelo de dados para o request
class ManifestacaoRequest(BaseModel):
    certificado: str  # Caminho para o certificado .pfx
    senha: str         # Senha do certificado
    uf: str            # UF (ex: 'PR')
    homologacao: bool  # True para homologação, False para produção
    cnpj: str          # CNPJ do destinatário
    chave: str         # Chave da nota fiscal
    operacao: int      # Tipo de operação (1 - Confirmada, 2 - Desconhecida, etc.)

@app.post("/manifestacoes", summary="Consulta o sistema da Sefaz", description="Códigos: Confirmação da Operação (código 1) – confirmando a ocorrência da operação e o recebimento da mercadoria (para as operações com circulação de mercadoria; Desconhecimento da Operação (código 3) – declarando o desconhecimento da operação; Operação Não Realizada (código 4) – declarando que a operação não foi realizada (com recusa do Recebimento da mercadoria e outros) e a justificativa do porquê a operação não se realizou; Ciência da Emissão (ou Ciência da Operação) (código 2) – declarando ter ciência da operação destinada ao CNPJ, mas ainda não possuir elementos suficientes para apresentar uma manifestação conclusiva, como as acima citadas. Este evento era chamado de Ciência da Operação.")
async def buscar_manifestacoes(request: ManifestacaoRequest):
    try:
        # Configuração do evento de manifestação
        manif_dest = EventoManifestacaoDest(
            cnpj=request.cnpj,
            chave=request.chave,
            data_emissao=datetime.datetime.now(),
            uf=request.uf,
            operacao=request.operacao,
        )

        # Serialização do evento
        serializador = SerializacaoXML(_fonte_dados, homologacao=request.homologacao)
        nfe_manif = serializador.serializar_evento(manif_dest)

        # Assinatura do XML
        assinatura = AssinaturaA1(request.certificado, request.senha)
        xml_assinado = assinatura.assinar(nfe_manif)

        # Comunicação com a SEFAZ
        comunicacao = ComunicacaoSefaz(request.uf, request.certificado, request.senha, request.homologacao)
        envio = comunicacao.evento(modelo='nfe', evento=xml_assinado)

        # Retorno da resposta em texto como lista de XMLs
        return {"status": "success", "xmls": [envio.text]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar manifestações: {str(e)}")
