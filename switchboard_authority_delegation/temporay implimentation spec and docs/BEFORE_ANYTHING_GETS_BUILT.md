Before anything gets built, I'd preserve the distinction between three things:
- Switchboard implementation: The machinery that discovers and resolves authorized handshakes.
- Switchboard contracts: The evidence establishing identity, authority, and delegation.
- Smart-code narration: The machinery that lets subsystems explain their actual responsibilities and operations.
They can live together without becoming one giant file.

and if the file has served its purpose and no longer rquired- it belongs in the gravyard. we respect the home of others

one principle for future Switchboard development:
Every authority change has three records: what changed, why it changed, and the evidence that justified it.
The code establishes the implementation. The contract establishes the intended authority. Git preserves the evolution of both.
