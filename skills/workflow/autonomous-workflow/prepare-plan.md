# Prepare or resume — Phases 0–2

Workflow material. Read when scope, acceptance, ownership or the remaining plan
needs to be established. Do not repeat this phase solely because a session resumed.

## Inputs

The user's current request and applicable prior decisions; project conventions;
existing plan/progress records; current checkout and any task baseline already saved.

## Actions

1. Identify the outcome, acceptance criteria, constraints and boundaries. Resolve
   routine choices from existing decisions and delegated judgment. Ask only about
   material ambiguity that cannot be resolved within that scope.
2. Inspect the relevant files and current checkout. For a new Git task, record
   the starting HEAD and initial `git status --short`; for a resumed task keep
   that original baseline and record the current status separately. Attribute
   pre-existing edits before changing overlapping content. If ownership is
   unresolved, pause that edit and continue independent work.
3. Reuse an existing record. Substantial work that needs recovery can use a brief
   and progress log; [records-reference.md](records-reference.md) gives an optional
   layout. Do not relocate or recreate valid project plans to adopt this layout.
4. Plan coherent, verifiable delivery units; one unit is valid. Each needs a goal,
   affected files, appropriate verification and an observable completion condition.
   Keep existing milestone IDs/names in reports and reviewer instructions.
5. Compare the proposed work with the user's scope, including public interfaces,
   dependencies, persistent data, trust boundaries and lifecycle changes. Preserve
   an approved threat model. An actual scope expansion needs a decision before
   implementation; a broad label such as "architecture" is not by itself a reason
   to pause a decision the user has already delegated.
6. Inspect exposed host restrictions relevant to the next actions. A local commit
   or other permission issue may affect execution, but do not run empty permission
   probes, change host settings or treat tool availability as user authorization.

Design exploration, scope audits and planning skills are optional aids for clearly
matched unresolved needs. Do not invoke them just to replay work already done.
A reference to a skill does not add its default approval pauses to this workflow.

## Output

An existing or updated record of the goal, acceptance criteria, plan, task baseline,
ownership and unresolved decisions. Include references needed by the next phase;
do not copy all repository guidance into the task record.

## Continue conditions

- Existing authorization covers the plan and no requested review remains:
  proceed to [implement.md](implement.md).
- The user requested one plan approval: present the concrete scope, delivery units
  and verification approach; reuse a matching explicit approval or wait for it.
- A necessary scope/ownership decision remains unresolved: present that specific
  decision and evidence. Continue work that does not depend on its answer.

Do not infer approval from silence or require the user to approve the same decision
again. If the work proves trivial, use proportionate execution without generating
the workflow's optional record structure.
