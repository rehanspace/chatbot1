male(saeed).
male(rehan).
male(faizan).
male(aqib).
male(saeed).
male(mustafa).
female(shazia).
female(amna).
female(fozia).
female(fatima).
female(summaiyah).
female(tasneem).
parent(saeed,shoaib).
parent(saeed,shahood).
parent(saeed,qasim).
parent(saeed,fatima).
parent(saeed,summaiyah).
parent(fazilat,shoaib).
parent(fazilat,shahood).
parent(fazilat,qasim).
parent(fazilat,fatima).
parent(fazilat,summaiyah).
parent(saeed,amna).
parent(tasneem,amna).
father(X, Y) :-parent(X, Y),male(X).
mother(X, Y) :-parent(X, Y),female(X).
brother(X, Y) :- male(X), sibling(X, Y).
sister(X, Y) :-female(X),sibling(X, Y).
sibling(X, Y) :-parent(Z, X),parent(Z, Y).
grandmother(X, Y) :-female(X),parent(X, Z), parent(Z, Y).
grandfather(X, Y) :-male(X),parent(X, Z),parent(Z, Y).
husband(X, Y) :- male(X), parent(X, Z), parent(Y, Z).
wife(X, Y) :- female(X), parent(X, Z), parent(Y, Z).
mother_sister(X, Y) :-mother(M, Y),sister(X, M).
father_brother(X, Y) :-father(F, Y),brother(X, F).
mother_brother(X, Y) :- mother(M, Y), brother(X, M).
father_sister(X, Y) :- father(F, Y),sister(X, F).

