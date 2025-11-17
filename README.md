❤️O pkgman é um gerenciador de pacotes completo e minimalista, desenvolvido com o objetivo de ser um substituto simples e acessível para gerenciadores como o pacman. Ele foi projetado para oferecer uma experiência clara, confiável e segura de gerenciamento de pacotes, mantendo uma estrutura limpa e totalmente transparente para o usuário.
Seu funcionamento é baseado em uma arquitetura modular que permite operações fundamentais, como:
Instalação de pacotes: baixa o pacote definido nos mirrors, extrai o conteúdo, organiza os arquivos no diretório de instalação e registra tudo no banco de dados interno.
Remoção de pacotes: remove todos os arquivos previamente instalados, limpa diretórios vazios e garante que não fiquem resíduos no sistema.
Query: permite consultar pacotes instalados, informações de versão, arquivos pertencentes e detalhes armazenados no banco de dados.
Triggers de segurança: caso qualquer etapa da instalação falhe — arquivos faltando, extração corrompida ou erro ao copiar — o sistema automaticamente executa um rollback, removendo qualquer modificação feita e restaurando backups criados antes da instalação.
Toda a configuração de servidores remotos é gerenciada através de um arquivo de mirrors localizado em:

~/.config/mirrors/config.txt

Esse arquivo centraliza as URLs utilizadas para download de pacotes, oferecendo flexibilidade para adicionar, remover ou reorganizar mirrors conforme necessário. Isso permite que o pkgman funcione tanto com repositórios locais quanto remotos, adaptando-se facilmente a diferentes ambientes.
Além disso, o projeto prioriza simplicidade interna e legibilidade: cada função é segmentada para que o usuário possa entender, modificar ou expandir o gerenciador conforme quiser — incluindo a adição futura de suporte a dependências, assinaturas, verificação de integridade e muito mais.
O pkgman é não apenas uma ferramenta funcional, mas também um excelente ponto de partida para quem deseja aprofundar conhecimentos sobre sistemas de pacotes, Python, automação e arquitetura de ferramentas CLI.
